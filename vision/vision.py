#!/usr/bin/env python3

import cv2

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()

    if not ret:
        print("Failed to capture frame")
        break
    
    cv2.imwrite("out.jpg", frame)