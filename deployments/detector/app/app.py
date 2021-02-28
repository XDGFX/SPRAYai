#!/usr/bin/env python3

"""
detector/app.py

Flask-based API webserver to handle inference requests for object detection.

Callum Morrison, 2021
"""

import cv2
import numpy as np
from flask import Flask, Response, abort, jsonify, request

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

    data = nn.bounding_box(img)

    return jsonify({
        "bounding_boxes": data,
        "count": len(data)
    })

@app.route('/api/detect/debug', methods=['POST'])
def detect_debug():
    r = request

    array = np.frombuffer(r.data, np.uint8)
    img = cv2.imdecode(array, cv2.IMREAD_COLOR)

    data = nn.bounding_box(img, visualise=True)

    _, img = cv2.imencode('.jpg', data)

    return Response(response=img.tostring(), status=200, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5050')
