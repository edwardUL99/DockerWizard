"""
This module provides working directory management as an abstraction to the functions provided by the os module
"""
import os
from collections import deque
import tempfile


# the previous working directories
_previous_directories = deque()


def _change_directory(directory: str):
    os.chdir(directory)


def change_directory(directory: str, not_store: bool = False):
    """
    Changes the directory to the provided directory, preserving the previous directory
    :param directory: the new working directory
    :param not_store: if true, the current working directory isn't added to the stack of maintained previous directories
    :return: None
    """
    if not not_store:
        _previous_directories.append(get_working_directory())
    _change_directory(directory)


def change_back():
    """
    Change back to the most previous working directory after a call to change_directory has been made
    :return: None
    """
    if len(_previous_directories) != 0:
        _change_directory(_previous_directories.pop())


def get_working_directory():
    """
    Gets the current working directory
    :return: current working directory
    """
    return os.getcwd()


def create_temp_directory():
    """
    Creates a temp directory for performing the build
    :return: the tempfile.TemporaryDirectory object
    """
    return tempfile.TemporaryDirectory()
