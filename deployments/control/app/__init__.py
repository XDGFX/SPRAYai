#!/usr/bin/env python3

"""
control/app

Flask-based API webserver to handle control over the Navvy smart sprayer.

Callum Morrison, 2021
"""

__version__ = "1.0.0"

import json
import re
import shutil
import subprocess
from threading import Lock, Thread

import redis
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from app import logs, settings

# Setup log
log = logs.create_log('host')
log = logs.append_redis(log, 'host', host='0.0.0.0')

app = Flask(__name__)

# sio = SocketIO(app, async_mode='threading')
sio = SocketIO(app)

# Initialise redis client database
r = redis.Redis(host='0.0.0.0', port='6379', db=0)
redis_lock = Lock()
r.set('client_list', json.dumps([]))
r.set('connections', json.dumps({}))

valid_namespaces = ["/pi", "/host", "/"]


def serve():
    sio.run(app, host='0.0.0.0', port='5040', debug=True)


def start_server():
    serve()
    # thread = Thread(target=serve)
    # thread.start()
    # log.info('Webserver started')


# --- WEBSERVER ROUTES ---
@app.route('/')
def index():
    with open('/proc/mounts', 'r') as f:
        # Get disk for root directory '/'
        drive = [line.split(' ')[0] for line in f.readlines()
                 if line.split(' ')[1] == '/'][0]
    usage = shutil.disk_usage('/')
    uptime = re.search('(\d+) hours, (\d+) minutes',
                       subprocess.check_output(['uptime', '-p'], encoding='UTF-8')).groups()

    properties = {
        "FIRMWARE": __version__,
        "EDITION": "beta",
        "UPDATE": "n/a",
        "DISK USAGE": f"{drive} {round(usage.used / usage.total * 100)}%",
        "UPTIME": f"{uptime[0]}h {uptime[1]}m"
    }
    return render_template('index.html', properties=properties)


@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/api/discover')
def discover():
    from flask import __version__
    return jsonify({
        'ping': 'pong',
        'flask_version': __version__,
        'navvy_spray_version': 'dev',
        'id': f'navvy_{request.args.get("id")}'
    })


@app.route('/api/emit/<namespace>')
def emit_request(namespace=None):
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

    return ('', 200)


@app.route('/api/settings')
def get_settings():
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


# --- WEBSOCKET ROUTES ---
@sio.event(namespace='/pi')
def register_client(client):

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


if __name__ == '__main__':
    start_server()
