"""
A module for loading custom commands
"""
import importlib
import yaml
import sys
import os

from .commands import AbstractCommand
from .errors import BuildConfigurationError


def _load_module(path: str):
    """
    Loads the module from the given path by using the directory of the path as the module (adding the directory path
    to sys.path if not there as the first element and removing it after import to avoid conflicts) and imports the
    module
    """
    if os.path.isfile(path) and path.endswith('.py'):
        module_dir = os.path.dirname(path)
        module = os.path.basename(path)
        module = module[0:module.index('.py')]
        inserted = False

        if module_dir not in sys.path:
            # insert as first in path to avoid conflicts with other modules
            sys.path.insert(0, module_dir)
            inserted = True  # mark that we inserted the module directory and not someone else so we can remove it

        module = importlib.import_module(module)

        if inserted:
            # we had to insert the module path ourselves, so remove it to avoid conflicts with modules of the same name
            sys.path.pop(0)

        return module
    else:
        raise BuildConfigurationError(f'Custom command file {path} is either not a file or Python (.py) file')


def _load_custom(command: dict):
    """
    Load the custom command from the command dictionary
    """
    path = command['file']
    class_name = command['class']

    module = _load_module(path)

    try:
        class_def = getattr(module, class_name)

        if issubclass(class_def, AbstractCommand):
            class_def()
        else:
            raise BuildConfigurationError(f'Command {class_name} from {path} does not extend AbstractCommand')
    except AttributeError:
        raise BuildConfigurationError(f'Class {class_name} does not exist within {path}')


def load_custom(commands_file: str):
    """
    Loads the custom commands into the system from the path to the commands file
    """
    with open(commands_file, 'r') as stream:
        data = yaml.safe_load(stream)

    if 'commands' in data:
        commands = data['commands']

        for command in commands:
            _load_custom(command)
