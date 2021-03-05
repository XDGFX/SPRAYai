#!/usr/bin/env python3

"""
test.py

Test the object detection API.

Callum Morrison, 2021
"""

import json
import time

import cv2
import numpy as np
import requests

# ------------------------------------------------

DEBUG = False

# ------------------------------------------------

addr = 'http://192.168.0.10:5050'
test_url = addr + '/api/detect'

if DEBUG:
    test_url = test_url + '/debug'

# prepare headers for http request
content_type = 'image/jpeg'
headers = {'content-type': content_type}

img = cv2.imread('test.jpg')
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

    if DEBUG:
        array = np.frombuffer(response.content, np.uint8)
        cv2.imwrite("detector/out.jpg", cv2.imdecode(array, cv2.IMREAD_COLOR))
        input("Press enter to continue...")
    else:
        print(json.loads(response.text))

    average_time = round((counter * average_time + duration) / (counter + 1))
    print(f"Average: {average_time}ms")

    counter += 1
    time.sleep(1)
    # decode response

# expected output: {u'message': u'image received. size=124x124'}
