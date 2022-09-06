"""
Provides utilities for displaying tool version
"""
import argparse
import platform

from .cli import info, error
from .const import DOCKER_WIZARD_CMD_NAME, VERSION, DOCKER_WIZARD_HOME
from .process import Execution


class VersionAction(argparse.Action):
    """
    An action that checks for a -v string and prints the version and exits if so
    """
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    @staticmethod
    def _print_docker_version():
        """
        Gets the docker version and prints an error if it can't be retrieved
        """
        result = Execution(['docker', '--version']).execute()

        if not result.is_healthy():
            error('Failed to retrieve Docker version information (Docker may not be installed)')
        else:
            info(f'Docker Installation: {result.stdout.strip()}')

    @staticmethod
    def _print_os_info():
        """
        Prints OS information
        """
        info(f'Python Version: {platform.python_version()}, OS: {platform.system()}, Version: {platform.release()},'
             f' Processor: {platform.processor()}')

    @staticmethod
    def _print_version():
        """
        Prints version and environment information
        """
        info(f'{DOCKER_WIZARD_CMD_NAME} version {VERSION}')
        info(f'DOCKER_WIZARD_HOME: {DOCKER_WIZARD_HOME}')
        VersionAction._print_docker_version()
        VersionAction._print_os_info()

    def __call__(self, parser, namespace, values, option_string=None):
        VersionAction._print_version()
        parser.exit()
