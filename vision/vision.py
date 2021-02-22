#!/usr/bin/env python3
"""
vision/vision.py

The camera-specific module; takes images and returns detected plants.

Callum Morrison, 2021
"""

import json
import os
import re
import time
from pathlib import Path
from queue import Queue

import cv2
import numpy as np
import redis
import requests
from dotenv import load_dotenv

import logs

# Setup log
log = logs.create_log(__name__)

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

# Initialise Redis
redis_url = re.match('([\d./:\w]+):([\d]+)',
                     os.environ.get('REDIS_URL')).groups()
r = redis.Redis(host=redis_url[0], port=redis_url[1], db=0)


class Camera():
    def __init__(self, sid):
        self.movement_key = f'movement--{sid}'
        self.cam = cv2.VideoCapture(0)
        # self.cam = cv2.VideoCapture(str(
        #     Path(__file__).parent.absolute() / '0000.mkv'))
        self.active = False

        self.frame_buffer = Queue()
        self.clear_buffer()

    def clear_buffer(self):
        """
        Clears frame and movement buffers.
        """
        self.frame_buffer.queue.clear()
        self.first_frame = None
        self.prev_frame = None

        r.set(self.movement_key, json.dumps((0, 0, 0)))

    def start_capture(self):
        """
        Start scheduled capture from the camera at a defined framerate.
        """
        log.info('Starting frame capture.')

        self.active = True

        start_time = time.time()

        while self.active:
            ret, frame = self.cam.read()

            # Check frame was correctly read
            if not ret:
                raise Exception('Unable to capture a frame!')

            # If first capture, save to first_frame, otherwise add to frame buffer
            if self.first_frame is None:
                self.first_frame = frame
            else:
                self.frame_buffer.put(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

            # Wait until next frame should be captured
            frame_wait = 1 / int(os.getenv('FRAMERATE_TRACK'))
            time.sleep(frame_wait - ((time.time() - start_time) % frame_wait))

    def start_track(self):
        """
        Track movement between each frame in the frame buffer using Lucas-Kanade Optical Flow.
        """
        self.track_err_count = 0

        while self.active:
            # Make sure queue doesn't get too long
            queue_length = len(self.frame_buffer.queue)
            if queue_length > int(os.getenv('FRAMERATE_TRACK')):
                log.warning(
                    f'Length of frame queue is getting long ({queue_length})!. Check that the processor is not overwhelmed.')

            # Make sure track error count is not too long
            if self.track_err_count >= 3:
                log.error(
                    f'Unable to track {self.track_err_count} frames in a row! There may be an issue with the camera')

            # If frame_buffer was recently cleared, wait for re-initialisation
            while (self.first_frame is None) or (len(self.frame_buffer.queue) == 0):
                time.sleep(0.01)

            # Setup frames
            new_frame = self.frame_buffer.get()
            prev_frame = self.prev_frame if self.prev_frame is not None else cv2.cvtColor(
                self.first_frame, cv2.COLOR_BGR2GRAY)

            # Setup track points
            prev_pts = cv2.goodFeaturesToTrack(prev_frame,
                                               maxCorners=200,
                                               qualityLevel=0.01,
                                               minDistance=30,
                                               blockSize=3)

            # Calculate optical flow
            new_pts, status, err = cv2.calcOpticalFlowPyrLK(
                prev_frame, new_frame, prev_pts, None)

            # Sanity check
            assert prev_pts.shape == new_pts.shape

            # Filter only valid points
            idx = np.where(status == 1)[0]
            prev_pts = prev_pts[idx]
            new_pts = new_pts[idx]

            try:
                # Find transformation matrix
                m = cv2.estimateAffinePartial2D(
                    prev_pts, new_pts)

                # Extract traslation
                dx = m[0][0][2]
                dy = m[0][1][2]

                # Extract rotation angle
                da = np.arctan2(m[0][1][0], m[0][0][0])

                log.debug(
                    f'Movement: {dx:5.2f}:{dy:5.2f}:{da:5.2f}')

                old_movement = json.loads(r.get(self.movement_key))
                new_pos = tuple(
                    map(lambda i, j: i + j, old_movement, (dx, dy, da)))

                r.set(self.movement_key, json.dumps(new_pos))

                self.track_err_count = 0
                self.prev_frame = new_frame

            except Exception as e:
                log.debug('Failed to calculate transformation', e)
                self.track_err_count += 1


def get_inference(img):
    """
    Send an image to the inference server and return the result.

    @return
    bbox        json list of bounding boxes
    """
    url = os.getenv('INFERENCE_URL') + '/api/detect'

    # Prepare headers for http request
    headers = {'content-type': 'image/jpeg'}

    # Encode image as jpeg
    _, img_encoded = cv2.imencode('.jpg', img)

    # Send http request with image and receive response
    try:
        response = requests.post(
            url,
            data=img_encoded.tostring(),
            headers=headers,
            timeout=int(os.getenv('INFERENCE_TIMEOUT')) / 1000
        )

        return json.loads(response.text)

    except requests.exceptions.ReadTimeout as e:
        log.error(e)

        return None
