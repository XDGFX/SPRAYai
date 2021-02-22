#!/usr/bin/env python3
"""
vision/host.py

Runs on Raspberry Pi's connected to vision cameras.
Used to communicate with the host and enable or disable spraying.

Callum Morrison, 2021
"""

import os
import queue
import socket
import time
from pathlib import Path
from threading import Thread

import socketio
from dotenv import load_dotenv

import logs
import vision

# Setup log
log = logs.create_log(__name__)

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

sio = socketio.Client()

# Initialise spraying queue
spray = queue.Queue(maxsize=1)

# --- SOCKETIO CONNECTION EVENTS ---


@sio.event(namespace='/pi')
def connect():
    log.info("Connected to host!")

    client = {
        "sid": sio.get_sid(namespace='/pi'),
        "hostname": socket.gethostname(),
        "addr": socket.gethostbyname(socket.gethostname())
    }

    log.info(client)

    # Register this client with the host
    sio.emit("register_client", client, namespace='/pi')


@sio.event(namespace='/pi')
def connect_error(msg):
    stop_spraying()
    log.error(f"The connection failed: {msg}")


@sio.event(namespace='/pi')
def disconnect():
    stop_spraying()
    log.warning("Disconnected from host!")


# --- SOCKETIO CUSTOM EVENTS ---

@sio.event(namespace='/pi')
def spray_enable():

    # Check if already spraying
    if len(spray.queue):
        log.info('Already spraying!')
        return

    # Clear the queue in a thread-safe manner
    with spray.mutex:
        spray.queue.clear()

    # Put something in the queue to trigger spraying
    spray.put(True)

    # Initialise camera
    cam = vision.Camera()

    # Enable frame capture
    t_cap = Thread(target=cam.start_capture)
    t_cap.start()

    # Start tracking movement
    t_track = Thread(target=cam.start_track)
    t_track.start()

    # Keep spraying while something is in the queue
    while len(spray.queue):
        log.info('Spraying')
        start_time = time.time()

        # Clear previous buffer
        cam.clear_buffer()

        # Wait for the first frame to capture
        while cam.first_frame is None:
            time.sleep(0.01)

        # Perform inference
        bbox = vision.get_inference(cam.first_frame)

        # Check if any detections were made
        if bbox['count'] == 0:
            log.info('No detections found! Not bothering to continue this frame.')

            # # Terminate video stream
            # cam.active = False

            # # Wait for camera thread to terminate
            # t_cap.join()

            # # Wait for track thread to terminate
            # t_track.join()

            # Wait until next frame should be captured
            frame_wait = 1 / float(os.getenv('FRAMERATE_INFERENCE'))
            log.info(f'Waiting {frame_wait}s')
            time.sleep(frame_wait - ((time.time() - start_time) % frame_wait))

            continue

        r = vision.get_plants()


@sio.event(namespace='/pi')
def spray_disable():
    stop_spraying()

    # --- MAIN FUNCTIONS ---


def connect_to_host():
    """
    Attempt to connect to the host device.
    """

    # Connect to the /pi namespace for Pi specific commands
    sio.connect(os.getenv('HOST_URL'), namespaces='/pi')


def stop_spraying():
    """
    Stop spraying immediately.
    """
    # Check if already spraying
    if len(spray.queue):
        # Clear spray queue
        with spray.mutex:
            spray.queue.clear()

        log.info('Spraying disabled')
    else:
        log.info('Already not spraying.')


if __name__ == "__main__":
    connect_to_host()
