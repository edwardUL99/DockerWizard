"""
This module encapsulates the parsing of required arguments
"""
from typing import List
from abc import ABC, abstractmethod
import argparse

from .builtincommands import BuiltinsHelpAction
from .const import DOCKER_WIZARD_CMD_NAME
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
        :param default: a default value (if callable, it will be called for a return value as default)
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
        :param default: a default value (if callable, it will be called for a return value as default)
        """
        super().__init__(name=name, description=description, action=action, required=required, default=default)
        self.long_name = long_name

    def add_to_parser(self, parser):
        default = self.default() if callable(self.default) else self.default
        parser.add_argument(self.name, self.long_name, help=self.description, action=self.action,
                            required=self.required, default=default)


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
        :param default: a default value (if callable, it will be called for a return value as default)
        :param nargs: number of args
        """
        super().__init__(name=name, description=description, action=action, required=required, default=default)
        self.nargs = nargs

    def add_to_parser(self, parser):
        default = self.default() if callable(self.default) else self.default
        parser.add_argument(self.name, help=self.description, action=self.action, default=default,
                            nargs=self.nargs)


def _get_parser() -> argparse.ArgumentParser:
    name = DOCKER_WIZARD_CMD_NAME

    return argparse.ArgumentParser(name, description='A tool to build Docker images with pre-build steps')


ARGUMENTS: List[Argument] = [
    PositionalArgument(name='file', description='The build file specifying the resulting Docker image. If '
                                                'not provided, a file called build.yaml will be looked '
                                                'up in the working directory', nargs='?'),
    FlagArgument(name='-c', long_name='--custom', description='A path to a custom commands YAML definition file. '
                                                              'Overrides default custom-commands.yaml file '
                                                              'found in the project root directory',
                 default=None, required=False),
    FlagArgument(name='-v', long_name='--version', description='Print the version of the tool and immediately exit',
                 required=False, action=VersionAction),
    FlagArgument(name='-b', long_name='--builtins', description='Print help information of all builtin commands and '
                                                                'immediately exit',
                 required=False, action=BuiltinsHelpAction)
]


def parse() -> argparse.Namespace:
    """
    Parse the defined arguments and return them in a namespace
    :return: the parsed arguments
    """
    parser = _get_parser()

    for arg in ARGUMENTS:
        arg.add_to_parser(parser)

    return parser.parse_args()
