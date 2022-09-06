"""
This module encapsulates the parsing of required arguments
"""
from typing import List
from abc import ABC, abstractmethod
import argparse

from .const import DOCKER_WIZARD_CMD_NAME
from .workdir import get_working_directory
from .versioning import VersionAction


class Argument:
    """
    The argument interface. Each implementation determines the arguments it requires
    """

    @abstractmethod
    def add_to_parser(self, parser):
        """
        Add the argument to the given parser in a means that makes sense to the implementing argument
        :param parser: tge parser to add the argument to
        """
        pass


class BaseArgument(Argument, ABC):
    """
    A base class for the argument
    """

    def __init__(self, *, name: str, description: str = None, action=None, required: bool = True, default=None):
        """
        Create a base argument
        :param name: the name of the argument. The format of the name depends on the implementing argument
        :param description: help description
        :param action: an action to perform with the arg, e.g, argparse store_true
        :param required: true if required (only valid if name and long_name is provided)
        :param default: a default value
        """
        self.name = name
        self.description = description
        self.action = action
        self.required = required
        self.default = default


class FlagArgument(BaseArgument):
    """
    Represents an argument that can be passed in as a flag with a short version and long, e.g. -f and --file. In the
    parsed args use the long name as the key
    """

    def __init__(self, *, name: str, long_name: str = None, description: str = None,
                 action=None, required: bool = True, default=None):
        """
        Create a flag argument
        :param name: the short flag name prefixed with -
        :param long_name: the long_name prefixed with --
        :param description: help description
        :param action: an action to perform with the arg, e.g, argparse store_true
        :param required: true if required (only valid if name and long_name is provided)
        :param default: a default value
        """
        super().__init__(name=name, description=description, action=action, required=required, default=default)
        self.long_name = long_name

    def add_to_parser(self, parser):
        parser.add_argument(self.name, self.long_name, help=self.description, action=self.action,
                            required=self.required, default=self.default)


class PositionalArgument(BaseArgument):
    """
    A positional argument that can have multiple or single values with no flag
    e.g. ./command arg
    """

    def __init__(self, *, name: str, description: str = None,
                 action=None, required: bool = True, default=None, nargs=None):
        """
        Create a flag argument
        :param name: the short flag name prefixed with -
        :param description: help description
        :param action: an action to perform with the arg, e.g, argparse store_true
        :param required: true if required (only valid if name and long_name is provided)
        :param default: a default value
        :param nargs: number of args
        """
        super().__init__(name=name, description=description, action=action, required=required, default=default)
        self.nargs = nargs

    def add_to_parser(self, parser):
        parser.add_argument(self.name, help=self.description, action=self.action, default=self.default,
                            nargs=self.nargs)


class GroupedArgument(Argument):
    """
    A mutual exclusion argument group to group args that only one value should be provided
    """
    def __init__(self, args: List[Argument]):
        self.args = args

    def add_to_parser(self, parser):
        group = parser.add_mutually_exclusive_group()

        for arg in self.args:
            arg.add_to_parser(group)


name = DOCKER_WIZARD_CMD_NAME
_parser = argparse.ArgumentParser(name, description='A tool to build Docker images with pre-build steps')
ARGUMENTS: List[Argument] = [
    PositionalArgument(name='file', description='The build file specifying the resulting Docker image'),
    FlagArgument(name='-w', long_name='--workdir', description='The working directory to run the tool from '
                                                               '(different to the build directory). The '
                                                               'build file will be sourced relative to this if '
                                                               'a relative path',
                 default=get_working_directory(), required=False),
    FlagArgument(name='-c', long_name='--custom', description='A path to a custom commands YAML definition file. '
                                                              'Overrides default custom-commands.yaml file '
                                                              'found in the project root directory',
                 default=None, required=False),
    FlagArgument(name='-v', long_name='--version', description='Print the version of the tool and immediately exit',
                 required=False, action=VersionAction)
]


_parsed = None


def parse() -> argparse.Namespace:
    """
    Parse the defined arguments and return them in a namespace
    :return: the parsed arguments
    """
    global _parsed

    if not _parsed:
        for arg in ARGUMENTS:
            arg.add_to_parser(_parser)

        _parsed = _parser.parse_args()

    return _parsed
