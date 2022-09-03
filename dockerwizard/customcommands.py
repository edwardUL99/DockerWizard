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
    if os.path.isfile(path) and path.endswith('.py'):
        module_dir = os.path.dirname(path)
        module = os.path.basename(path)
        module = module[0:module.index('.py')]

        if module_dir not in sys.path:
            sys.path.append(module_dir)

        return importlib.import_module(module)
    else:
        raise BuildConfigurationError(f'Custom command file {path} is either not a file or Python (.py) file')


def _load_custom(file: dict):
    path = file['file']
    class_name = file['class']

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
    with open(commands_file, 'r') as stream:
        data = yaml.safe_load(stream)

    if 'commands' in data:
        commands = data['commands']

        for command in commands:
            _load_custom(command)
