#!/usr/bin/env python3
"""
vision/spray.py

The spray-specific module; controls and actuates the sprayer.

Callum Morrison, 2021
"""

import os
import queue
import time
from pathlib import Path
from threading import Thread

from dotenv import load_dotenv

import logs

# Setup log
log = logs.create_log(__name__)

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

# Initialise spraying queue
spray_queue = queue.Queue(maxsize=1)

inference_wait = 1 / float(os.getenv('FRAMERATE_INFERENCE'))


class Spray():
    def __init__(self, sid):
        import vision

        # Initialise camera
        self.cam = vision.Camera(sid=sid)

        # Initialise servos
        self.servo = vision.Servo(
            sid=sid,
            img_width=self.cam.cam.resolution[0],
            img_height=self.cam.cam.resolution[1]
        )

    def start_spraying(self):
        """
        Main logic for overall spray program.
        """

        # Check if already spraying
        if len(spray_queue.queue):
            log.info('Already spraying!')
            return

        # Clear the queue in a thread-safe manner
        with spray_queue.mutex:
            spray_queue.queue.clear()

        # Put something in the queue to trigger spraying
        spray_queue.put(True)

        # Enable frame capture
        t_cap = Thread(target=self.cam.start_capture)
        t_cap.start()

        # Start tracking movement
        t_track = Thread(target=self.cam.start_track)
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

        log.info('Spraying...')

        # Keep spraying while spraying is active
        while len(spray_queue.queue):

            # Clear previous buffer
            self.cam.clear_buffer()

            # Wait for the first frame to capture
            while self.cam.first_frame is None:
                time.sleep(0.01)

            # Perform inference
            bbox = self.cam.get_inference(self.cam.first_frame)

            # Check that the request was successful
            if bbox is None:
                continue

            # Check if any detections were made
            if bbox['count'] == 0:
                log.debug(
                    'No detections found! Not bothering to continue this frame.')

                # Wait until next frame should be captured
                time.sleep(inference_wait -
                           ((time.time() - start_time) % inference_wait))

                continue

            log.info(bbox)

            if os.environ.get('DEBUG_TRACK').lower() in ['true', 't', '1']:
                # Save frames for debugging
                original_inference = self.cam.draw_bounding_boxes(
                    self.cam.first_frame, bbox)
                bbox = self.servo.correct_bbox(bbox)
                corrected_inference = self.cam.draw_bounding_boxes(
                    self.cam.frame_buffer.get(), bbox)

                self.cam.write_image(original_inference,
                                     f'original/{frame_count:04}.jpg')
                self.cam.write_image(corrected_inference,
                                     f'corrected/{frame_count:04}.jpg')

                frame_count += 1

            # Convert bounding boxes to centre points to spray
            original_points = [self.servo.bbox2centre(
                bbox['bounding_boxes'][i]) for i in range(bbox['count'])]

            # Order points starting at the bottom (largest y)
            ordered_points = sorted(
                original_points, key=lambda point: point[1], reverse=True)

            # Spray each point
            total_spray_start_time = time.time()
            for point in ordered_points:

                # Check if spraying has been disabled
                if not len(spray_queue.queue):
                    break

                # Check that spray time has not been exceeded
                if time.time() > total_spray_start_time + self.servo.spray_total_time:
                    log.warning(
                        'Ran out of time to spray all plants in this image')
                    log.warning(
                        f'Consider increasing SPRAY_TOTAL_TIME if possible (currently: {self.servo.spray_total_time}s)')
                    break

                # Do this twice to ensure initial spray is relatively accurate
                for i in range(2):
                    # Make initial correction
                    new_point = self.servo.correct_point(point)

                    # Move sprayer to position
                    self.servo.goto_point(new_point, prev_point)
                    prev_point = new_point

                # Start spraying
                self.servo.spray(enable=True)

                spray_start_time = time.time()

                # Keep tracking while spraying
                while time.time() < spray_start_time + self.servo.spray_per_plant:
                    new_point = self.servo.correct_point(point)
                    self.servo.goto_point(new_point, prev_point)
                    prev_point = new_point

                # Stop spraying
                self.servo.spray(enable=False)

        # Stop spraying
        self.servo.spray(enable=False)

        # Terminate video stream
        self.cam.active = False

        # Wait for camera thread to terminate
        t_cap.join()

        # Wait for track thread to terminate
        t_track.join()

    def stop_spraying(self):
        """
        Stop spraying immediately.
        """
        # Check if already spraying
        if len(spray_queue.queue):
            # Clear spray queue
            with spray_queue.mutex:
                spray_queue.queue.clear()

            log.info('Spraying disabled')
        else:
            log.info('Already not spraying.')
