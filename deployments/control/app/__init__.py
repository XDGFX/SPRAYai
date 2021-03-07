#!/usr/bin/env python3

"""
control/app

Flask-based API webserver to handle control over the Navvy smart sprayer.

Callum Morrison, 2021
"""

import json
from threading import Thread, Lock

import redis
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

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
    # print('Webserver started')


# --- WEBSERVER ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/discover')
def discover():
    from flask import __version__
    return jsonify({
        'ping': 'pong',
        'flask_version': __version__,
        'navvy_spray_version': 'dev',
        'id': f'navvy_{request.args.get("id")}'
    })


@app.route('/emit/<namespace>')
def emit_pi(namespace=None):
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

    print(f'Received emit request: {cmd} for namespace {namespace}')
    sio.emit(cmd, namespace=namespace)

    return ('', 200)


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

    print(f'Registered client: {client}')

    r.set('client_list', json.dumps(client_list))
    r.set('connections', json.dumps(connections))

    redis_lock.release()


@sio.event(namespace='/pi')
def connect():
    print(f'{request.sid} just connected to /pi')


@sio.event(namespace='/pi')
def disconnect():
    print(f'{request.sid} has disconnected from /pi')

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
    except IndexError:
        print('A client disconnected before it was fully registered.')
        print(f'sid: {request.sid}')

    redis_lock.release()


@sio.event(namespace='/host')
def connect():
    print(f'{request.sid} just connected to /host')


@sio.event(namespace='/host')
def disconnect():
    print(f'{request.sid} has disconnected from /host')


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
        print('Missing command or namespace')

    # Add leading slash
    namespace = f"/{namespace}"

    if namespace not in valid_namespaces:
        print(f'Invalid namespace: {namespace}')

    print(f'Received emit request: {cmd} for namespace {namespace}')
    sio.emit(cmd, namespace=namespace)


if __name__ == '__main__':
    start_server()
