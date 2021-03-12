#!/usr/bin/env python3
"""
control/utils.py

General utilities which may be used in any module.

Callum Morrison, 2021
"""

import re
import subprocess

import redis

r = redis.Redis(host='0.0.0.0', port='6379', db=0)


class LiveUpdater():
    """
    Storage of all variables to be used in the live updater.
    """

    def _code(self, variable_name):
        """
        Template JavaScript code for injecting into the HTML.
        """
        return f"""
        <span id=live_updater:{variable_name}></span>
        <script>
            elm = document.getElementById("live_updater:{variable_name}")

            socket.on("live_updater:{variable_name}", data => {{
                console.log("Got data")
                elm.innerText = data;
            }});

            setInterval(function() {{
                socket.emit("live_updater", "{variable_name}")
            }}, 1000);
        </script>
        """

    def uptime(self):
        """
        Returns the system uptime in a nicely formatted string.
        """
        uptime = re.search('up (\d+):(\d+)',
                           subprocess.check_output(['uptime'], encoding='UTF-8')).groups()

        return f"{uptime[0]}h {uptime[1]}m"

    def spraying(self):
        """
        Returns 'Spraying' or 'Not spraying' according to the current system status.
        """
        return "Spraying" if int(r.get('spraying')) else "Not spraying"

    uptime = property(uptime)
    spraying = property(spraying)
