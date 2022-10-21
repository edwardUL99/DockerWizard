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
from .errors import BuildConfigurationError
from . import timing


def _validate_file(file):
    """
    Validate the filepath
    :param file: the build file to validate
    :return: validated filepath
    """
    file = file if file else 'build.yaml'
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


def _find_custom_command_path(args_path: str, workdir: str, home_path: str):
    """
    Finds custom commands path in the order:
    args_path - path passed in with -c arg
    workdir - relative to working directory
    home_path - looks for custom command file in docker wizard home
    """
    paths = [
        args_path,
        os.path.join(workdir, CUSTOM_COMMANDS),
        os.path.join(home_path, CUSTOM_COMMANDS)
    ]

    for i, path in enumerate(paths):
        if path and os.path.isfile(path):
            return path
        elif i == 0 and args_path is not None:
            # index 0 is the file provided by -c and if it is not found, throw an error
            raise BuildConfigurationError(f'Custom commands file {args_path} not found')

    return None


def _load_custom_commands(custom_command_path: str):
    """
    Loads the custom commands if such a definition file exists
    :param custom_command_path: the path to the custom commands definition file
    :return: None
    """
    if custom_command_path and not os.path.isabs(custom_command_path):
        custom_command_path = os.path.join(get_working_directory(), custom_command_path)

    try:
        custom_command_path = _find_custom_command_path(custom_command_path, get_working_directory(),
                                                        _docker_wizard_home())
    except BuildConfigurationError as e:
        cli.error(e.message)
        sys.exit(1)

    if custom_command_path is not None:
        validation_error = custom_command_path_validator(custom_command_path)

        if not validation_error:
            change_directory(os.path.dirname(custom_command_path))
            load_custom(os.path.basename(custom_command_path))
            change_back()
        else:
            cli.error(validation_error)
            sys.exit(1)


def main():
    """
    The main entrypoint
    :return: None
    """
    timing.start()
    initialise_system()

    args = parse()

    custom_command_path = args.custom

    _change_working_dir(args.workdir)
    _load_custom_commands(custom_command_path)
    file = _validate_file(args.file)

    parser = get_build_parser()
    parsed = parser.parse(file)
    builder_obj = Builder(parsed)

    built = builder_obj.build()
    timing.end()
    duration = timing.get_duration()

    cli.info(f'Duration: {duration}')

    if not built:
        cli.error('BUILD FAILED')
        sys.exit(1)
    else:
        cli.info('BUILD SUCCEEDED')
        change_back()
