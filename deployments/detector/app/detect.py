#!/usr/bin/env python3

"""
detect.py

Python integration of the YOLOv4 darknet object detection.
Designed to work as part of an API webserver, returning a JSON response.

Callum Morrison, 2021
"""

import json

import cv2
import pycuda.autoinit  # Create CUDA context
import pycuda.driver as cuda 

from src.yolo_with_plugins import get_input_shape, TrtYOLO  # From jkjung-avt/tensorrt_demos

dev = cuda.Device(0)  # Select GPU 0
ctx = dev.make_context()

model = "yolov4-tiny-416x416"
num_categories = 2
conf_threshold = 0.5    # Required confidence score for response


class Detector():
    """
    Main Detector class.
    Initialises by loading the neural network and configuring variables.
    """

    def __init__(self):
        """
        Loads the model into the class, speeding up inference.
        """

        h, w = get_input_shape(model)
        self.trt_yolo = TrtYOLO(model, (h, w), num_categories)

    def bounding_box(self, image, visualise=False):
        """
        Detect objects within the supplied image, and return their bounding boxes.
        """
        ctx.push()  # For thread safety
        boxes, _, _ = self.trt_yolo.detect(image, conf_threshold)
        ctx.pop()

        # Convert to Python lists
        boxes = [[float(elm) for elm in box] for box in boxes]

        return boxes