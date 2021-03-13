#!/usr/bin/env python3
"""
control/utils.py

General utilities which may be used in any module.

Callum Morrison, 2021
"""

import json
import shutil
import time

import redis

r = redis.Redis(host='0.0.0.0', port='6379', db=0)


class LiveUpdater():
    """
    Storage of all variables to be used in the live updater.
    """

    def __init__(self, log):
        self.system_start_time = None
        self.log = log

    def _code(self, variable_name, polling_rate=1000, placeholder=""):
        """
        Template JavaScript code for injecting into the HTML.

        variable_name   The name of the variable to synchronise with Python
        polling_rate    How often (in ms) to update the variable
        placeholder     The default text before an update is received
        """
        return f"""
        <span id=live_updater_{variable_name}>{placeholder}</span>
        <script>
            // Perform initial request
            socket.emit("live_updater", "{variable_name}")

            // Function to update span text
            socket.on("live_updater_{variable_name}", data => {{
                document.getElementById("live_updater_{variable_name}").innerText = data;
            }});

            // Function to update variable at polling_rate
            setInterval(function() {{
                socket.emit("live_updater", "{variable_name}")
            }}, {polling_rate});
        </script>
        """

    def uptime(self):
        """
        Returns the system uptime in a nicely formatted string.
        """

        # Only read system uptime once, then store the start time
        # in a class variable to prevent the need for re-opening the file
        if self.system_start_time is None:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = round(float(f.readline().split()[0]))
                self.system_start_time = round(time.time() - uptime_seconds)
        else:
            uptime_seconds = time.time() - self.system_start_time

        # Convert to human readable format
        mins, sec = divmod(uptime_seconds, 60)
        hour, mins = divmod(mins, 60)

        return f"{hour:.0f}h {mins:0.0f}m {sec:02.0f}s"

    def spraying(self):
        """
        Returns 'Spraying' or 'Not spraying' according to the current system status.
        """
        return "Spraying" if int(r.get('spraying')) else "Not spraying"

    def usage(self):
        """
        Checks disk usage on mount point '/'.
        """
        with open('/proc/mounts', 'r') as f:
            drive = [line.split(' ')[0] for line in f.readlines()
                     if line.split(' ')[1] == '/'][0]

        usage = shutil.disk_usage('/')

        return (drive, round(usage.used / usage.total * 100))

    def nozzles(self, hostname=None):
        """
        Returns data about a specific nozzle for updating the UI.
        """
        client_list = json.loads(r.get('client_list'))

        # Return a specific client, otherwise return all
        if hostname is not None:
            # Check that the client exists
            try:
                client_list = [
                    client for client in client_list if client['hostname'] == hostname]

                if len(client_list) == 0:
                    raise IndexError

            except IndexError:
                self.log.warning(f"The client {hostname} could not be found!")
                response = [{
                    "hostname": hostname,
                    "connection": "not connected",
                    "latency": "Latency: n/a",
                    "logs": 0
                }]

                return response

        response = [{
            "hostname": client["hostname"],
            "connection": "connected",
            "latency": "Latency: " + str(round(float(r.get(f"pong--{client['sid']}")) * 1000)) + "ms",
            "logs": 1
        } for client in client_list]

        return response

    uptime = property(uptime)
    spraying = property(spraying)
