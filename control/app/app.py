#!/usr/bin/env python3

"""
control/app.py

Flask-based API webserver to handle control over the Navvy smart sprayer.

Callum Morrison, 2021
"""

import threading
from flask import Flask, request, render_template
from flask_socketio import SocketIO
from threading import Thread

app = Flask(__name__)
# sio = SocketIO(app, async_mode='threading')
sio = SocketIO(app)

# Client_list is a big list of all connected clients, and includes information about the client.
client_list = []

# Connections is a dictionary in the form {sid: index} where `index` is the location of the client in client_list with sid=sid
connections = {}

valid_namespaces = ["/pi", "/host", "/"]


def serve():
    sio.run(app, host='0.0.0.0', port='5040')


def start_server():
    thread = Thread(target=serve)
    thread.start()
    print('Webserver started')


# --- WEBSERVER ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')


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

    # Register the client in the client_list
    index = len(client_list)
    client_list.append(client)
    connections[request.sid] = index

    print(client_list)

    print(f'Registered client: {client}')


@sio.event(namespace='/pi')
def connect():
    print(f'{request.sid} just connected to /pi')


@sio.event(namespace='/pi')
def disconnect():
    print(f'{request.sid} has disconnected from /pi')

    # Remove that client from the client_list
    index = connections[request.sid]
    del connections[request.sid]
    del client_list[index]


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
