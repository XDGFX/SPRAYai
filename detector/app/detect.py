#!/usr/bin/env python3

"""
detect.py

Python integration of the YOLOv4 darknet object detection.
Designed to work as part of an API webserver, returning a JSON response.

Callum Morrison, 2021
"""

import json

import cv2
import numpy as np

config_file = "yolov4-tiny.cfg"
weights_file = "yolov4-tiny.weights"
conf_threshold = 0.5    # Required confidence score for response
nms_threshold = 0.4     # Non maximal supression threshold


class Detector():
    """
    Main Detector class.
    Initialises by loading the neural network and configuring variables.
    """

    def __init__(self):
        """
        Loads the model into the class, speeding up inference.
        """

        self.net = cv2.dnn.readNet(weights_file, config_file)

        # Specify to use CUDA
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    def get_output_layers(self, net):
        """
        Retreive the output layer names in the architecture.
        """

        layer_names = net.getLayerNames()

        output_layers = [layer_names[i[0] - 1]
                         for i in net.getUnconnectedOutLayers()]

        return output_layers

    def bbox(self, image):
        """
        Detect objects within the supplied image, and return their bounding boxes.
        """
        Width = image.shape[1]
        Height = image.shape[0]
        scale = 0.00392

        # Create input blob
        blob = cv2.dnn.blobFromImage(
            image, scale, (416, 416), (0, 0, 0), True, crop=False)

        # Set input blob for the network
        self.net.setInput(blob)

        # Run inference
        outs = self.net.forward(self.get_output_layers(self.net))

        # Initialisation
        class_ids = []
        confidences = []
        boxes = []

        # Loop over each detection
        for out in outs:
            for detection in out:

                # Collect confidence for checking
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                # Ignore weak detections
                if confidence > conf_threshold:
                    center_x = int(detection[0] * Width)
                    center_y = int(detection[1] * Height)
                    w = int(detection[2] * Width)
                    h = int(detection[3] * Height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

        # Apply non-maximal suppression
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, conf_threshold, nms_threshold)
        output = [boxes[i[0]] for i in indices]

        return json.dumps(output)
