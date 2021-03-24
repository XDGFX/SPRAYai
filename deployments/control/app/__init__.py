#!/usr/bin/env python3

"""
control/app

Flask-based API webserver to handle control over the Navvy smart sprayer.

Callum Morrison, 2021
"""

__version__ = "1.0.0"

import crypt
import json
import os
import time
from hmac import compare_digest
from threading import Lock, Thread

import redis
from flask import (Flask, Response, abort, jsonify, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO

from app import logs, settings, util

# Setup log
log = logs.create_log('host')
log = logs.append_redis(log, 'host')

app = Flask(__name__)

# sio = SocketIO(app, async_mode='threading')
sio = SocketIO(app)

# Initialise redis client database
r = redis.Redis(os.environ.get('REDIS_HOST') or '0.0.0.0', port='6379', db=0)

redis_lock = Lock()
r.set('client_list', json.dumps([]))
r.set('connections', json.dumps({}))

valid_namespaces = ["/pi", "/host", "/"]

valid_logins = {
    "admin": "$6$08qess8qYJJwcgQv$4M3qmg1U.Rt5yQU8GIt9wl6PCPaMoG5avQzVWnjVccRpfQcQZX7k.1lVMUeg14ZtQBt2pzm1NbsmOhqeavH1R/"
}

updater = util.LiveUpdater(log)


def serve():
    app.secret_key = os.urandom(12)
    # sio.run(app, host='0.0.0.0', port='5040', debug=True)
    sio.run(app, host='0.0.0.0', port='5040')


def start_server():
    # Start heartbeat for nozzles (ping)
    sio.start_background_task(target=heartbeat)

    # Ensure spraying is disabled
    spray(0)

    serve()
    # start_in_thread(serve)
    log.info('Webserver started')


# --- WEBSERVER ROUTES ---
@app.route('/')
def route_index():
    # Check if user is logged in
    if not session.get('logged_in'):
        error = request.args.get('login_error')
        return render_template('login.html', error=error)

    usage = updater.usage()
    properties = {
        "FIRMWARE": __version__,
        "EDITION": "beta",
        "UPDATE": "n/a",
        "DISK USAGE": f"{usage[0]} {usage[1]}%"
    }
    return render_template('index.html', properties=properties, spraying=int(r.get('spraying')), client_list=json.loads(r.get('client_list')))


@app.route('/login', methods=['POST'])
def route_login():
    username = request.form.get('username').lower()
    password = request.form.get('password')

    password_hash = valid_logins.get(username)

    if not password_hash:
        return redirect("/?login_error=user_not_found")

    match = compare_digest(crypt.crypt(password, password_hash), password_hash)

    if match:
        session['logged_in'] = True
        return redirect("/")
    else:
        return redirect("/?login_error=password_match")


@app.route('/settings', methods=['GET', 'POST'])
def route_settings():
    # Check if user is logged in
    if not session.get('logged_in'):
        error = request.args.get('login_error')
        return render_template('login.html', error=error)

    if request.method == "GET":
        return render_template('settings.html', settings=settings.get_settings())

    elif request.method == "POST":
        # Check if submitted or canceled
        cancel = request.form.get("cancel")

        if cancel:
            return redirect('/')

        new_settings = {}

        for setting, value in request.form.items():
            if setting.startswith('setting_') and value:
                # Convert to correct format
                new_settings[setting[len('setting_'):].upper()] = value.upper()

        # If any new settings exist
        if new_settings:
            settings.update_settings(new_settings)

        return redirect('/')

    else:
        return (f"Unrecognised method: {request.method}", 405)


@app.route('/test')
def route_test():
    return render_template('test.html')


@app.route('/api/discover')
def api_discover():
    from flask import __version__
    return jsonify({
        'ping': 'pong',
        'flask_version': __version__,
        'navvy_spray_version': 'dev',
        'id': f'navvy_{request.args.get("id")}'
    })


@app.route('/api/emit/<namespace>')
def api_emit_request(namespace=None):
    """
    Emit custom command to a specific namespace
    REST API version
    """
    cmd = request.args.get('cmd')

    # Validate request
    if not (cmd and namespace):
        return ('Missing command or namespace', 400)

    # Add leading slash
    namespace = f"/{namespace}"

    if namespace not in valid_namespaces:
        return (f'Invalid namespace: {namespace}', 405)

    log.debug(f'Received emit request: {cmd} for namespace {namespace}')
    sio.emit(cmd, namespace=namespace)

    return (f'Sent "{cmd}" on namespace: {namespace}', 200)


@app.route('/api/settings')
def api_get_settings():
    """
    Return global settings. If param 'keys' is None, returns all keys.
    Otherwise, only returns settings requested by 'keys'.
    """
    keys = request.args.get('keys')

    # Return all settings by default
    if keys is None:
        return jsonify(settings.get_settings())
    else:
        keys = keys.split(',')

        return_settings = []
        all_settings = settings.get_settings()

        for item in all_settings:
            if item.get('key') in keys:
                return_settings.append(item)

        return jsonify(return_settings)


@app.route('/api/logs')
def api_get_logs():
    """
    Get the text file of all logs for the host with query parameter 'hostname'.
    """
    hostname = request.args.get('hostname')

    # The number of lines to return, default: 1000 if not provided.
    lines = request.args.get('lines') or 1000

    # Check that a hostname was requested
    if hostname is None:
        abort(400)

    logs = r.lrange(f"log--{hostname}", 0, lines)

    # Wrap into a generator so the whole list isn't generated at once
    def generate():
        for line in logs:
            yield line.decode() + "\n"

    return Response(
        generate(),
        mimetype="text/log",
        headers={"Content-disposition":
                 f"attachment; filename={hostname}.log"}
    )


# --- LIVE UPDATER ---
@app.context_processor
def utility_processor():
    def live_updater(variable_name):
        """
        Returns the bespoke JavaScript code for auto-updating a variable with name `variable_name`.
        """
        return updater._code(variable_name)
    return dict(live_updater=live_updater)


@sio.event(namespace='/host')
def live_updater(variable_name):
    """
    Echos the value of property `variable_name` saved in the live updater class over WebSocket.
    """
    sio.emit(f"live_updater_{variable_name}", getattr(
        updater, variable_name), namespace="/host")


# --- HEARTBEAT ---
def heartbeat():
    """
    Measure the latency of connected clients intermittently.
    """
    while True:
        ping_time = time.time()
        sio.emit('ping', namespace='/pi')
        r.set("ping_time", str(ping_time))

        sio.sleep(3)


@sio.event(namespace='/pi')
def pong():
    pong_time = time.time()
    ping_time = float(r.get("ping_time"))
    r.set(f"pong--{request.sid}", (pong_time - ping_time) / 2)


# --- WEBSOCKET ROUTES ---
@sio.event(namespace='/pi')
def register_client(client):
    """
    Add a nozzle client to the Redis client database.
    """

    redis_lock.acquire()
    client_list = json.loads(r.get('client_list'))
    connections = json.loads(r.get('connections'))

    # Register the client in the client_list
    index = len(client_list)
    client_list.append(client)
    connections[request.sid] = index

    log.info(f'Registered client: {client}')

    r.set('client_list', json.dumps(client_list))
    r.set('connections', json.dumps(connections))

    redis_lock.release()


@sio.event(namespace='/pi')
@sio.event(namespace='/host')
def connect():
    log.info(f'{request.sid} just connected to {request.namespace}')


@sio.event(namespace='/pi')
@sio.event(namespace='/host')
def disconnect():
    log.info(f'{request.sid} has disconnected from {request.namespace}')

    if request.namespace == '/pi':
        redis_lock.acquire()
        client_list = json.loads(r.get('client_list'))
        connections = json.loads(r.get('connections'))

        # Remove that client from the client_list
        try:
            index = connections[request.sid]
            del connections[request.sid]
            del client_list[index]

            r.set('client_list', json.dumps(client_list))
            r.set('connections', json.dumps(connections))

        except (KeyError, IndexError):
            log.warning(
                f'A client disconnected before it was fully registered. ({request.sid})')

        redis_lock.release()


@sio.event(namespace='/host')
def emit(data):
    """
    Emit custom command to a specific namespace
    WebSocket version
    """
    # Validate request
    cmd = data['cmd']
    namespace = data['namespace']

    if not (cmd and namespace):
        log.warning('Missing command or namespace')
        return

    # Add leading slash
    namespace = f"/{namespace}"

    if namespace not in valid_namespaces:
        log.warning(f'Invalid namespace: {namespace}')
        return

    log.debug(f'Received emit request: {cmd} for namespace {namespace}')
    sio.emit(cmd, namespace=namespace)


@sio.event(namespace='/host')
def spray(option):
    """
    Start or stop spraying.

    option:
    0   Stop spraying
    1   Start smart spraying
    2   Start blanket spraying
    """

    if option == 1:
        log.info('Received request to start smart spraying')
        r.set('spraying', 1)
        sio.emit('spray_enable', namespace='/pi')
    elif option == 2:
        log.info('Received request to start blanket spraying')
        r.set('spraying', 2)
        sio.emit('spray_enable_blanket', namespace='/pi')
    else:
        log.info('Received request to stop spraying')
        r.set('spraying', 0)
        sio.emit('spray_disable', namespace='/pi')


@sio.event(namespace='/host')
def nozzle_status(hostname):
    """
    Echos the current nozzle status for updating the UI.
    """
    try:
        sio.emit(f"nozzle_status_{hostname}",
                 json.dumps(updater.nozzles(hostname)[0]), namespace="/host")
    except IndexError:
        # The device is no longer connected, ignore the request.
        pass


if __name__ == '__main__':
    start_server()
