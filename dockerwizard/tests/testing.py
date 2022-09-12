"""
A wrapper around unittest
"""
import contextlib
import os
from typing import Dict
import unittest
from unittest.mock import MagicMock, patch

from dockerwizard.const import DOCKER_WIZARD_TESTING_NAME

os.environ[DOCKER_WIZARD_TESTING_NAME] = 'True'


def test_join(path: str, *paths: str):
    """
    A platform independent test implementation of os.path.join to be used in mocking
    """
    for p in paths:
        path = f'{path}/{p}'

    return path


def patch_os_path():
    """
    A utility function to make a mock of commonly used methods of os.path
    """
    mocked_path = MagicMock()
    mocked_path.abspath = MagicMock()
    mocked_path.isdir = MagicMock()
    mocked_path.isfile = MagicMock()
    mocked_path.isabs = MagicMock()
    mocked_path.join = test_join
    mocked_path.dirname = os.path.dirname
    mocked_path.basename = os.path.basename
    mocked_path.abspath.side_effect = lambda x: x

    return mocked_path


class PatchedDependencies:
    """
    A class that creates and manages multiple patches
    """
    def __init__(self, patches: Dict[str, str]):
        """
        Initialise the patches where key is the name to bind the patch to and
        value is the dependency to patch
        to bind to the patched object
        """
        self._created_patches: Dict[str, any] = {}
        self._create_patches(patches)

    def _create_patches(self, patches: Dict[str, str]):
        """
        Creates the patches
        """
        for key, value in patches.items():
            self._created_patches[key] = patch(value)

    def get(self, key) -> MagicMock:
        """
        Get the attribute identified by key
        """
        return self.__getattribute__(key)

    def __enter__(self):
        """
        On entry activate all the patches, assigning the activated patches to the object
        using setattr
        """
        for key, value in self._created_patches.items():
            self.__setattr__(key, value.start())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        On exit, the patch is stopped and the activated patch is remove from the object using delattr
        """
        for key, value in self._created_patches.items():
            value.stop()
            self.__delattr__(key)

        self._created_patches = {}


def main():
    """
    This method should be called instead of unittest.main as it sets required environment variables
    """
    unittest.main()