#!/usr/bin/env python3

"""
actuate_spray.py

Takes a list of detected plant positions, and sprays them in the most efficient manner.
Uses a redis server to store persistent variables (robot speed, last actuator position etc.)

Variables:
- Spray time per plant
- Max total time (based on speed of robot, ensures all plants are sprayed)
- Equation to relate coordinates to spray angle
- Max spray angle speed (to calculate delay while nozzle is moving)
"""

import random
import time

import redis
from pymata4 import pymata4

# Database setup
r = redis.Redis(host='localhost', port=6379,
                db=0, decode_responses=True)

# Arduino setup
board = pymata4.Pymata4()
servo_pin = 9
spray_pin = 5

# Variables
spray_per_plant = 0.25  # seconds
total_time = 3          # seconds
angle_rate = 240        # degrees per second

# Multiplier to get from distance to angle, may change this to tan(angle) = dist / height
dist2angle = 20


def _setup():
    """
    Used to setup the redis database for testing
    """
    r.set("current_speed", 1)  # 1 m/s

    # Setup Arduino output
    board.set_pin_mode_servo(servo_pin)
    board.set_pin_mode_digital_output(spray_pin)

    board.servo_write(servo_pin, 180)
    time.sleep(180 / angle_rate)
    board.servo_write(servo_pin, 0)
    time.sleep(180 / angle_rate)


def shortest_route(plants, current_position):
    """
    Calculate the best route between each plant in the array, `plants`.

    It does this by first going to the side with the closest *far point*,
    and completing all points on that side, before returning to the other side.

    This allows the shortest 'return distance' from one side, back to the start,
    and then to the other side, and resultantly the shortest total distance.

    @return
    Sorted list
    """

    # Direction is True if shortest route is higher points first, then lower.
    direction = (current_position - min(plants)
                 ) > (max(plants) - current_position)

    # Check if current position must be sprayed first
    if current_position in plants:
        route = [current_position]
        plants.remove(current_position)
    else:
        route = []

    # Separate elements
    route_high, route_low = [], []
    for x in plants:
        if x > current_position:
            route_high.append(x)
        else:
            route_low.append(x)

    # Sort elements
    route_high.sort()
    route_low.sort(reverse=True)

    # Create fastest route
    if direction:
        route = [route, route_high, route_low]
    else:
        route = [route, route_low, route_high]

    # Remove empty
    route = [x for sublist in route for x in sublist if x]

    return route


def spray(plants):
    """
    Main spray control

    @input
    plants:     a list containing x coordinates e.g. [11, 25, 75]
    """

    if not plants:
        # No plants in this image
        return 0

    # Save the current speed. Assume speed will remain constant until plants are sprayed
    current_speed = float(r.get("current_speed"))

    if not current_speed:
        raise Exception(f"Current robot speed is invalid: {current_speed}")

    # Request the latest nozzle position
    nozzle_position = float(r.get("nozzle_position") or 0)

    # Find shortest route, may need to convert nozzle_position to current_position
    route = shortest_route(plants, nozzle_position)

    last_position = nozzle_position

    for item in route:

        # Calculate time to reach position
        wait_time = abs(last_position - item) * dist2angle / angle_rate
        last_position = item

        # Move nozzle to position
        board.servo_write(servo_pin, int(item * dist2angle))
        time.sleep(wait_time)

        # Activate sprayer for specified time
        print(f"Spraying {item}")
        board.digital_pin_write(spray_pin, 1)
        time.sleep(spray_per_plant)
        board.digital_pin_write(spray_pin, 0)
        print(f"Finished spraying {item}")

    r.set("nozzle_position", last_position)


if __name__ == "__main__":
    # For testing only
    _setup()

    while True:
        number_spray_points = random.randint(0, 10)
        test_points = [random.randint(0, 9)
                       for _ in range(number_spray_points)]

        # Remove duplicates
        spray_points = []
        [spray_points.append(x) for x in test_points if x not in spray_points]

        print(spray_points)
        spray(spray_points)
