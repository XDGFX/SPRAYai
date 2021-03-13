#!/usr/bin/env python3
"""
vision/host.py

Runs on Raspberry Pi's connected to vision cameras.
Used to communicate with the host and enable or disable spraying.

Callum Morrison, 2021
"""

import os
import socket
import time
from pathlib import Path

import socketio
from dotenv import load_dotenv

import logs
import spray

# Setup log
log = logs.create_log('host')

# Load environment variables
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path)

sio = socketio.Client()


# --- SOCKETIO CONNECTION EVENTS ---
@sio.event(namespace='/pi')
def connect():
    sid = sio.get_sid(namespace='/pi')

    # Attach Redis to log handler
    global log
    log = logs.append_redis(log, redis_key=socket.gethostname())

    log.info("Connected to host!")

    global s
    s = spray.Spray(sid=sid, log=log)

    client = {
        "sid": sid,
        "hostname": socket.gethostname(),
        "addr": get_ip(),
        "conn_time": round(time.time()),
        "latency": -1
    }

    log.info(client)

    # Register this client with the host
    sio.emit("register_client", client, namespace='/pi')


@sio.event(namespace='/pi')
def connect_error(msg):
    log.error(f"The connection failed: {msg}")
    disconnect_clean()


@sio.event(namespace='/pi')
def disconnect():
    log.warning("Disconnected from host!")
    disconnect_clean()


# --- SOCKETIO CUSTOM EVENTS ---
@sio.event(namespace='/pi')
def spray_enable():
    try:
        s.start_spraying()
    except NameError:
        log.error(
            'A spray request was received before the device has been registered. Wait a few seconds and try again.')


@sio.event(namespace='/pi')
def spray_disable():
    try:
        s.stop_spraying()
    except NameError:
        log.error(
            'A spray request was received before the device has been registered. Wait a few seconds and try again.')


@sio.event(namespace='/pi')
def ping():
    sio.emit('pong', namespace='/pi')


# --- MAIN FUNCTIONS ---
def connect_to_host():
    """
    Attempt to connect to the host device.
    """
    connection_attempts = 0
    connected = False

    while not connected:

        if connection_attempts >= 10:
            log.error(
                f'Unable to connect to the host at {os.environ.get("HOST_URL")} after {connection_attempts} tries.')
            auto_discover_host()

        try:
            # Check if host url has been defined
            if not os.environ.get('HOST_URL'):
                auto_discover_host()

            # Connect to the /pi namespace for Pi specific commands
            sio.connect(os.environ.get('HOST_URL'), namespaces='/pi')
            connected = True

        except Exception as e:
            connection_attempts += 1
            log.error(e)
            log.warning(
                f'Unable to connect to the WebSocket server at {os.environ.get("HOST_URL")}')
            log.warning(
                f'Attempting to reconnect (Attempt: {connection_attempts}/10)')

            time.sleep(1)


def get_ip():
    """
    Gets the LAN ip address, even if /etc/hosts contains localhost or if there is no internet connection.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable
        sock.connect(('10.255.255.255', 1))
        ip = sock.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        sock.close()
    return ip


def update_env(key, value):
    """
    Update the .env file with a new key, value pair. Overwrites identical keys, or appends if the key doesn't exist.
    """
    env_exists = Path(env_path).is_file()
    env_updated = False

    if env_exists:
        with open(env_path, 'r') as f:
            data = f.readlines()

        # Check if key already exists
        for index, line in enumerate(data):

            # Add trailing newline to all lines
            if not line.endswith('\n'):
                data[index] = line + '\n'

            if line.startswith(key):
                # Update existing value
                data[index] = f'{key}={value}\n'
                env_updated = True
                break

        if not env_updated:
            data.append(f'{key}={value}\n')

    else:
        # File doesn't exist yet
        data = [f'{key}={value}\n']

    with open(env_path, 'w') as f:
        f.writelines(data)

    # Reload the environment variables
    load_dotenv(dotenv_path=env_path, override=True)


def auto_discover_host():
    """
    Attempt to automatically discover the host machine by pinging
    all IPs in the current subnet.
    """
    import random
    import string
    from concurrent.futures import ThreadPoolExecutor, as_completed

    import requests

    def test_url(url):
        """
        Check if url is the correct host server.
        """
        try:
            log.info(f'Trying url: {url}')
            # Make request
            params = {
                'id': ''.join(random.choice(string.ascii_letters) for _ in range(10))
            }
            r = requests.get(url, params=params, timeout=2)

            # Validate server is correct
            log.info(f'Found service at url: {url}')
            return r.json()['id'] == f'navvy_{params["id"]}'

        except Exception as e:
            log.debug(e)
            return False

    log.info('Performing automatic host discovery...')

    # Find subnet from host ip
    subnet = get_ip().split('.')[0:-1]

    # Assume network is /24 (possible IPs from 1-255)
    addr = range(1, 256)
    port = '5040'
    ips = [
        f"http://{'.'.join(subnet)}.{x}:{port}/api/discover" for x in addr]

    # Ping endpoints 10 at a time for performance
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_ip = {executor.submit(
            test_url, ip): ip for ip in ips}

        for future in as_completed(future_ip):
            if future.result():

                # Assign correct IP to environment variable
                ip = future_ip[future]
                update_env('HOST_URL', ip.rstrip('/api/discover'))

    # Check if a host was found
    if not os.environ.get('HOST_URL'):
        log.error(
            'No host url was found automatically. Will retry in 5 seconds...')
        time.sleep(5)
        auto_discover_host()

    else:
        log.info(
            f'Using auto-discovered host at url: {os.environ.get("HOST_URL")}')


def disconnect_clean():
    """
    Ensures all connections and devices are closed allowing for a clean shutdown or reconnection.
    """
    log.info('Attempting a clean disconnect...')
    s.stop_spraying()

    # Wait for spraying thread to finish
    time.sleep(2)

    log.info('Disconnecting camera')
    s.cam.cam.close()

    log.info('Disconnecting Arduino')
    s.servo.a.shutdown()

    # Ensure everything is closed properly
    time.sleep(2)

    log.info('Everything is properly disconnected')


if __name__ == "__main__":
    connect_to_host()
