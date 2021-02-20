#!/usr/bin/env python3

"""
control/app.py

Flask-based API webserver to handle control over the Navvy smart sprayer.

Callum Morrison, 2021
"""

from flask import Flask, request
from flask_socketio import SocketIO, send, emit
from threading import Thread

app = Flask(__name__)
sio = SocketIO(app)

# Client_list is a big list of all connected clients, and includes information about the client.
client_list = []

# Connections is a dictionary in the form {sid: index} where `index` is the location of the client in client_list with sid=sid
connections = {}

def serve():
    sio.run(app, host="0.0.0.0", port="5040")

def start_server():
    thread = Thread(target=serve)
    thread.start()
    print("Webserver started")

# --- WEBSERVER ROUTES ---
@app.route('/')
def index():
    return 'Control system webserver is working!'

# --- WEBSOCKET ROUTES ---
@sio.on('register_client')
def register_client(client):

    # Register the client in the client_list
    index = len(client_list)
    client_list.append(client)
    connections[request.sid] = index


@sio.event
def connect():
    print(request.sid)
    print("Something connected!")

@sio.event
def disconnect():
    print(f"{request.sid} has disconnected")

    # Remove that client from the client_list
    index = connections[request.sid]
    del connections[request.sid]
    del client_list[index]
