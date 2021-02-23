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
import spray
import vision

# Setup log
log = logs.create_log(__name__)

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

inference_wait = 1 / float(os.getenv('FRAMERATE_INFERENCE'))

sio = socketio.Client()

# Initialise spraying queue
spray = queue.Queue(maxsize=1)

# Initialise camera
cam = vision.Camera(sid=sio.get_sid(namespace='/pi'))

# Initialise servos
servo = vision.Servo(
    sid=sio.get_sid(namespace='/pi'),
    img_width=cam.cam.get(3),
    img_height=cam.cam.get(4)
)


# --- SOCKETIO CONNECTION EVENTS ---
@sio.event(namespace='/pi')
def connect():
    log.info("Connected to host!")

    client = {
        "sid": sio.get_sid(namespace='/pi'),
        "hostname": socket.gethostname(),
        "addr": socket.gethostbyname(socket.gethostname()),
        "conn_time": round(time.time())
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

    start_spraying()


@sio.event(namespace='/pi')
def spray_disable():
    stop_spraying()


# --- MAIN FUNCTIONS ---
def connect_to_host():
    """
    Attempt to connect to the host device.
    """

    connection_attempts = 0
    connected = False

    while not connected:
        try:
            # Connect to the /pi namespace for Pi specific commands
            sio.connect(os.getenv('HOST_URL'), namespaces='/pi')
            connected = True

        except Exception as e:
            connection_attempts += 1
            log.error(e)
            log.warning(
                f'Unable to connect to the WebSocket server at {os.getenv("HOST_URL")}')
            log.warning(
                f'Attempting to reconnect (Attempt: {connection_attempts})')

            time.sleep(1)


def start_spraying():
    """
    Main logic for overall spray program.
    """

    # Enable frame capture
    t_cap = Thread(target=cam.start_capture)
    t_cap.start()

    # Start tracking movement
    t_track = Thread(target=cam.start_track)
    t_track.start()

    prev_point = (0, 0)

    start_time = time.time()

    if os.environ.get('DEBUG_TRACK').lower() in ['true', 't', '1']:
        import shutil

        for path in ['original', 'corrected']:
            if os.path.isdir(path):
                shutil.rmtree(path)

            os.mkdir(path)

        frame_count = 0

    # Keep spraying while spraying is active
    while len(spray.queue):
        log.info('Spraying')

        # Clear previous buffer
        cam.clear_buffer()

        # Wait for the first frame to capture
        while cam.first_frame is None:
            time.sleep(0.01)

        # Perform inference
        bbox = cam.get_inference(cam.first_frame)

        # Check that the request was successful
        if bbox is None:
            continue

        # Check if any detections were made
        if bbox['count'] == 0:
            log.info('No detections found! Not bothering to continue this frame.')

            # Wait until next frame should be captured
            time.sleep(inference_wait -
                       ((time.time() - start_time) % inference_wait))

            continue

        if os.environ.get('DEBUG_TRACK').lower() in ['true', 't', '1']:
            # Save frames for debugging
            original_inference = cam.draw_bounding_boxes(cam.first_frame, bbox)
            bbox = servo.correct_bbox(bbox)
            corrected_inference = cam.draw_bounding_boxes(
                cam.frame_buffer.get(), bbox)

            cam.write_image(original_inference,
                            f'original/{frame_count:04}.jpg')
            cam.write_image(corrected_inference,
                            f'corrected/{frame_count:04}.jpg')

            frame_count += 1

        # Convert bounding boxes to centre points to spray
        original_points = [servo.bbox2centre(
            bbox['bounding_boxes'][i]) for i in range(bbox['count'])]

        # Order points starting at the bottom (largest y)
        ordered_points = sorted(
            original_points, key=lambda point: point[1], reverse=True)

        # Spray each point
        total_spray_start_time = time.time()
        for point in ordered_points:

            # Check that spray time has not been exceeded
            if time.time() > total_spray_start_time + servo.spray_total_time:
                log.warning(
                    'Ran out of time to spray all plants in this image')
                log.warning(
                    f'Consider increasing SPRAY_TOTAL_TIME if possible (currently: {servo.spray_total_time}s)')
                break

            # Do this twice to ensure initial spray is relatively accurate
            for i in range(2):
                # Make initial correction
                new_point = servo.correct_point(point)

                # Move sprayer to position
                servo.goto_point(new_point, prev_point)
                prev_point = new_point

            # Start spraying
            servo.spray(enable=True)

            spray_start_time = time.time()

            # Keep tracking while spraying
            while time.time() < spray_start_time + servo.spray_per_plant:
                new_point = servo.correct_point(point)
                servo.goto_point(new_point, prev_point)
                prev_point = new_point

            # Stop spraying
            servo.spray(enable=False)

    # Terminate video stream
    cam.active = False

    # Wait for camera thread to terminate
    t_cap.join()

    # Wait for track thread to terminate
    t_track.join()


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
