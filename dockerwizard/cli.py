"""
A module for printing to the command line
"""
import os
import sys

from .system import register_system_initialisation, SystemInitialisation, OSTypes
from .const import DOCKER_WIZARD_TESTING_NAME

register_system_initialisation(SystemInitialisation(OSTypes.WINDOWS, lambda: os.system('color')))
register_system_initialisation(SystemInitialisation(OSTypes.ALL, lambda: _set_disable_color()))

__all__ = ['info', 'warn', 'error']

_RED = '\u001b[31m'
_GREEN = '\u001b[32m'
_YELLOW = '\u001b[33m'
_RESET = '\u001b[0m'

_INFO = 'INFO'
_WARN = 'WARNING'
_ERROR = 'ERROR'

_DISABLED = False
_DISABLE_COLOR = False
_DISABLE_COLOR_VAR = 'DOCKER_WIZARD_DISABLE_COLOR'


def _set_disable_color():
    global _DISABLE_COLOR
    if os.environ.get(_DISABLE_COLOR_VAR) is not None:
        _DISABLE_COLOR = True


def _disabled():
    return _DISABLED or os.environ.get(DOCKER_WIZARD_TESTING_NAME) == 'True'


def _create_message(color: str, message: str, level: str) -> str:
    """
    Create the message with given log level and color
    :param color: the color to create the message with
    :param message: the message to wrap
    :param level: the log level
    :return: the created message
    """
    header = f'[{color}{level}{_RESET}]' if not _DISABLE_COLOR else f'[{level}]'
    message = '' if message is None else f' {message}'
    return f'{header}{message}'


def _print(msg: str, use_stderr: bool = False):
    """
    Print the message if cli is not disabled
    """
    if not _disabled():
        if not use_stderr:
            print(msg)
        else:
            print(msg, file=sys.stderr)


def info(message: str = None):
    """
    Print an info message
    :param message: the info message to print
    :return: None
    """
    _print(_create_message(_GREEN, message, _INFO))


def warn(message: str):
    """
    Print a warning message
    :param message: the warning message
    :return: None
    """
    _print(_create_message(_YELLOW, message, _WARN))


def error(message: str):
    """
    Log an error message
    :param message: the error message
    :return: None
    """
    _print(_create_message(_RED, message, _ERROR), True)


def disable():
    """
    Disable output from the cli module
    """
    global _DISABLED
    _DISABLED = True


def enable():
    """
    Enable output from the cli module
    """
    global _DISABLED
    _DISABLED = False
