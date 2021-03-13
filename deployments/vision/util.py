#!/usr/bin/env python3
"""
vision/utils.py

General utilities which may be used in any module.

Callum Morrison, 2021
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)


def get_setting(keys, complete=False):
    """
    Gets the setting value from the host.

    keys:       Can be a single key string, multiple key string separated by commas, or a list of keys.
    complete:   If True returns the whole setting, otherwise just the 'value'
    """
    ip = os.environ.get('HOST_URL') + '/api/settings'
    params = {
        'keys': keys if isinstance(keys, str) else ','.join(keys)
    }

    r = requests.get(ip, params=params)

    if r.status_code == 200:
        return r.json()[0].get('value')
    else:
        return None
