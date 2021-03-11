#!/usr/bin/env python3
"""
logs.py

General log handling and formatting.

Callum Morrison, 2021
"""

import logging
import os
import re

import redis


class CustomFormatter(logging.Formatter):
    """
    Logging Formatter to add colors and count warning / errors
    """
    grey = "\x1b[38m"
    blue = "\x1b[96m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;7mm"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class RedisLogHandler():
    def __init__(self, redis_key, host):
        self.formatter = logging.Formatter(
            '%(asctime)s--%(name)s--%(levelname)s--%(message)s')
        self.redis_list_key = 'log--' + redis_key
        self.level = logging.DEBUG

        # Create Redis connection
        host_url = host or re.search('([\d.]+):',
                                     os.environ.get('HOST_URL')).groups()[0]
        self.redis = redis.Redis(host=host_url, port='6379', db=0)

    def handle(self, record):
        try:
            self.redis.lpush(self.redis_list_key,
                             self.formatter.format(record))
            self.redis.ltrim(self.redis_list_key, 0,
                             int(os.environ.get('REDIS_LOG_LENGTH') or 10000))
        except:
            # Not much can be done, likely Redis is not accessible
            pass


def create_log(name):
    """
    Create the default stream logger
    """
    log = logging.getLogger(name)

    if os.environ.get("LOG_LEVEL") == "DEBUG":
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Add streamhandler to logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Apply log formatting
    ch.setFormatter(CustomFormatter())

    log.addHandler(ch)

    return log


def append_redis(log, redis_key, host=None):
    """
    Append the Redis log handler to an existing log.
    """
    rh = RedisLogHandler(redis_key=redis_key, host=host)
    log.addHandler(rh)

    return log
