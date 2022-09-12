"""
The main entrypoint into the module
"""
import os
import sys

from .const import CUSTOM_COMMANDS, DOCKER_WIZARD_HOME_VAR
from .workdir import get_working_directory, change_directory, change_back
from . import cli
from .argparser import parse
from .builder import Builder
from .buildparser import get_build_parser
from .customcommands import load_custom, custom_command_path_validator
from .system import initialise_system, docker_wizard_home


def _validate_file(file):
    """
    Validate the filepath
    :param file: the build file to validate
    :return: validated filepath
    """
    path = os.path.join(get_working_directory(), file)

    if not os.path.isfile(path):
        cli.error(f'Build file {file} does not exist')
        sys.exit(1)
    else:
        return path


def _change_working_dir(working_dir):
    """
    Change to the specified working directory
    :param working_dir: the new working directory
    :return: NOne
    """
    abspath = os.path.abspath(working_dir)

    if abspath != get_working_directory():
        if not os.path.isdir(abspath):
            cli.error(f'{working_dir} does not exist')
            sys.exit(2)

        cli.info(f'Changing directory to {abspath}')
        change_directory(abspath)


def _docker_wizard_home():
    """
    A wrapper around docker_wizard_home to do more validations
    :return: the docker wizard home path
    """
    var = docker_wizard_home()

    if not os.path.isabs(var):
        cli.warn(
            f'{DOCKER_WIZARD_HOME_VAR} {var} is not an absolute path so it is relative to where the tool is run from. '
            'This is not recommended')

    return var


def _load_custom_commands(custom_command_path: str):
    """
    Loads the custom commands if such a definition file exists
    :param custom_command_path: the path to the custom commands definition file
    :return: None
    """
    provided = custom_command_path is not None
    custom_command_path = custom_command_path if provided else \
        os.path.join(docker_wizard_home(), CUSTOM_COMMANDS)
    validation_error = custom_command_path_validator(custom_command_path)

    if not validation_error:
        change_directory(os.path.dirname(custom_command_path))
        load_custom(os.path.basename(custom_command_path))
        change_back()
    elif provided:
        cli.error(validation_error)
        sys.exit(1)


def main():
    """
    The main entrypoint
    :return: None
    """
    initialise_system()

    # change directory as custom commands and other system initialisations are done relative to docker builder home
    change_directory(_docker_wizard_home())
    args = parse()
    _load_custom_commands(args.custom)
    change_back()  # now change back to where script was called from

    _change_working_dir(args.workdir)
    file = _validate_file(args.file)

    parser = get_build_parser()
    parsed = parser.parse(file)
    builder_obj = Builder(parsed)

    if not builder_obj.build():
        sys.exit(1)
    else:
        change_back()
