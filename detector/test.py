#!/usr/bin/env python3

"""
test.py

Test the object detection API.

Callum Morrison, 2021
"""

import json
import time

import cv2
import requests

addr = 'http://192.168.0.27:5050/'
test_url = addr + '/api/detect'

# prepare headers for http request
content_type = 'image/jpeg'
headers = {'content-type': content_type}

img = cv2.imread('detector/test.jpg')
# encode image as jpeg
_, img_encoded = cv2.imencode('.jpg', img)
# send http request with image and receive response

counter = 0
average_time = 0

while True:
    start_time = time.time()
    response = requests.post(
        test_url, data=img_encoded.tostring(), headers=headers)
    duration = round((time.time() - start_time) * 1000)
    print(f"Inference performed in {duration}ms")
    print(json.loads(response.text))

    average_time = round((counter * average_time + duration) / (counter + 1))
    print(f"Average: {average_time}ms")

    counter += 1
    # decode response

# expected output: {u'message': u'image received. size=124x124'}
