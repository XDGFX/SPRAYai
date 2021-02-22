#!/usr/bin/env python3
"""
vision/spray.py

The spray-specific module; controls and actuates the sprayer.

Callum Morrison, 2021
"""

import json
import os
import re
import time
from pathlib import Path

import redis
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


def print_movement(sid):
    movement_key = f'movement--{sid}'

    for i in range(100):
        print(json.loads(r.get(movement_key)))
        time.sleep(0.1)
