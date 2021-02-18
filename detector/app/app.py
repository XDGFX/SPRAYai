#!/usr/bin/env python3

"""
app.py

Flask-based API webserver to handle inference requests for object detection.

Callum Morrison, 2021
"""

import cv2
import numpy as np
from flask import Flask, Response, abort, request

from detect import Detector

app = Flask(__name__)
nn = Detector()


@app.route('/')
def index():
    return 'Please use the API at the /api endpoint'


@app.route('/api/detect', methods=['POST'])
def detect():
    r = request

    array = np.frombuffer(r.data, np.uint8)
    img = cv2.imdecode(array, cv2.IMREAD_COLOR)

    data = nn.bbox(img)

    return Response(response=data, status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5050')
