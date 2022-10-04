"""
A module to allow for timing of the tool's execution
"""
import math
import time
from datetime import timedelta

_start_time = 0
_end_time = 0


def start():
    """
    Start the timing module
    """
    global _start_time
    _start_time = time.time()


def end():
    """
    End the timing module
    """
    global _end_time
    _end_time = time.time()


def get_duration():
    """
    Gets a formatted duration of how long the timing module was in executing between start() and end() as a string
    """
    duration = _end_time - _start_time
    delta = str(timedelta(seconds=duration))

    # split string into individual component
    x = delta.split(':')

    return f'{x[0]}H:{x[1]}M:{math.floor(float(x[2]))}S'
