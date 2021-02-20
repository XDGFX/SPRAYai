#!/usr/bin/env python3


import socket

import socketio

sio = socketio.Client()

URL = "http://192.168.0.27:5040"


@sio.event
def connect():
    print("I'm connected!")

    client = {
        "sid": sio.get_sid(),
        "hostname": socket.gethostname(),
        "addr": socket.gethostbyname(socket.gethostname())
    }

    print(client)

    sio.emit("register_client", client)


@sio.event
def connect_error(msg):
    print(f"The connection failed: {msg}")


@sio.event
def disconnect():
    print("I'm disconnected!")


if __name__ == "__main__":
    sio.connect(URL)
