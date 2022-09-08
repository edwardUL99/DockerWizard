"""
A module for printing to the command line
"""
import os
import sys

from .system import register_system_initialisation, SystemInitialisation, OSTypes

register_system_initialisation(SystemInitialisation(OSTypes.WINDOWS, lambda: os.system('color')))

__all__ = ['info', 'warn', 'error']

_RED = '\u001b[31m'
_GREEN = '\u001b[32m'
_YELLOW = '\u001b[33m'
_RESET = '\u001b[0m'

_INFO = 'INFO'
_WARN = 'WARNING'
_ERROR = 'ERROR'


def _create_message(color: str, message: str, level: str) -> str:
    """
    Create the message with given log level and color
    :param color: the color to create the message with
    :param message: the message to wrap
    :param level: the log level
    :return: the created message
    """
    return f'[{color}{level}{_RESET}] {message}'


def info(message: str):
    """
    Print an info message
    :param message: the info message to print
    :return: None
    """
    print(_create_message(_GREEN, message, _INFO))


def warn(message: str):
    """
    Print a warning message
    :param message: the warning message
    :return: None
    """
    print(_create_message(_YELLOW, message, _WARN))


def error(message: str):
    """
    Log an error message
    :param message: the error message
    :return: None
    """
    print(_create_message(_RED, message, _ERROR), file=sys.stderr)
