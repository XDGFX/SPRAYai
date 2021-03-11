#!/usr/bin/env python3

"""
control/settings

Handles storage and modification of global sprayer settings.

Callum Morrison, 2021
"""

import json
from pathlib import Path

settings_file_default = Path(
    __file__).parent.absolute() / 'settings.default.json'
settings_file = Path(
    __file__).parent.absolute() / 'settings.json'

if not Path(settings_file).is_file():
    with settings_file.open('w+') as f:
        f.write(json.dumps(json.loads(settings_file_default.read_text())))


def get_settings():
    """
    Get latest settings list.
    """
    return json.loads(settings_file.read_text())


def set_settings(settings):
    """
    Save settings to file.
    """
    with settings_file.open('w+') as f:
        f.write(json.dumps(settings))
