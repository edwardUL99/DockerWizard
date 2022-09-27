"""
Provides the library for integration test verifications
"""
import os
from os import environ
import platform
from unittest import main as _ut_main, TestCase

import yaml


class PostVerificationTestCase(TestCase):
    """
    The class which all post verification steps should take place in.
    Standard output can be accessed in self.stdout and error output of the build
    can be found in self.stderr. exit code can be accessed by self.exit_code
    Super must be called and subclass init methods must have same signature.
    """
    def __init__(self, methodName):
        super().__init__(methodName)
        self.stdout = ''
        self.stderr = ''
        self.exit_code = int(environ.get('DOCKER_BUILD_TEST_CODE'))
        self._read_files()

    def _read_files(self):
        with open('stdout.txt', 'r') as f:
            self.stdout = f.read().strip()

        with open('stderr.txt', 'r') as f:
            self.stderr = f.read().strip()

    def read_program_envs(self, program):
        """
        Reads a mock programs environment variables if they exist and have been output by mock programs
        """
        path = f'{program.upper()}_envs.yaml'

        if os.path.isfile(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return None

    def verify_env_variable(self, env_variables, key, expected):
        """
        Reads from given environment variables and asserts that the value with key equals expected
        """
        if platform.system() == 'Windows':
            key = key.upper()

        self.assertEqual(env_variables[key], expected)


def main():
    """
    Call this method to start the script
    """
    _ut_main()
