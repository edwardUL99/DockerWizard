"""
Tests the custom commands module
"""
import contextlib
import unittest
from unittest.mock import patch

from .testing import main, PatchedDependencies, patch_os_path
from dockerwizard.commands import AbstractCommand
from dockerwizard import customcommands
from dockerwizard.errors import BuildConfigurationError

base_package = 'dockerwizard.customcommands'

workdir = '/path/workdir'
commands_path = f'{workdir}/custom-commands.yaml'

test_command = {
    'commands': [
        {
            'file': 'custom.py',
            'class': 'TestCustomCommand'
        }
    ]
}

test_invalid_command = {
    'commands': [
        {
            'file': 'custom',
            'class': 'TestCustomCommand'
        }
    ]
}


class StubbedCommand(AbstractCommand):
    def __init__(self):
        super().__init__('', 0)

    def _execute(self, args: list):
        pass


class StubbedModule:
    def __init__(self, return_none: bool = False):
        self._none = return_none

    def _execute(self, args: list):
        pass

    def __getattr__(self, item):
        if self._none:
            raise AttributeError
        else:
            return StubbedCommand


class CustomCommandsTests(unittest.TestCase):
    def setUp(self) -> None:
        customcommands._LOADED_MODULES = {}

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'importlib': f'{base_package}.importlib',
            'yaml': f'{base_package}.yaml',
            'sysPatch': f'{base_package}.sys',
            'osPatch': f'{base_package}.os',
            'getWorkDir': f'{base_package}.get_working_directory',
            'changeDir': f'{base_package}.change_directory',
            'changeBack': f'{base_package}.change_back',
            'openPatch': 'builtins.open'
        }) as patched:
            patched.osPatch.path = patch_os_path()

            yield patched

    def test_load_custom(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('yaml').safe_load.return_value = test_command
            patched.get('osPatch').path.isfile.return_value = True
            patched.get('osPatch').path.isabs.return_value = False
            patched.get('osPatch').path.dirname.return_value = workdir
            patched.get('osPatch').path.basename.return_value = 'custom.py'
            patched.get('getWorkDir').return_value = workdir
            patched.get('sysPatch').path = []
            patched.get('importlib').import_module.return_value = StubbedModule()

            customcommands.load_custom('custom-commands.yaml')

            patched.get('yaml').safe_load.assert_called()
            patched.get('osPatch').path.isfile.assert_called()
            patched.get('osPatch').path.isabs.assert_called()
            patched.get('getWorkDir').assert_called()
            patched.get('importlib').import_module.assert_called()

    def test_load_custom_not_file(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('yaml').safe_load.return_value = test_command
            patched.get('osPatch').path.isfile.return_value = False
            patched.get('osPatch').path.isabs.return_value = False

            with self.assertRaises(BuildConfigurationError):
                customcommands.load_custom('custom-commands.yaml')

            patched.get('yaml').safe_load.assert_called()
            patched.get('osPatch').path.isfile.assert_called()
            patched.get('osPatch').path.isabs.assert_not_called()
            patched.get('getWorkDir').assert_not_called()
            patched.get('importlib').import_module.assert_not_called()

    def test_load_custom_not_py_file(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('yaml').safe_load.return_value = test_invalid_command
            patched.get('osPatch').path.isfile.return_value = True
            patched.get('osPatch').path.isabs.return_value = False

            with self.assertRaises(BuildConfigurationError):
                customcommands.load_custom('custom-commands.yaml')

            patched.get('yaml').safe_load.assert_called()
            patched.get('osPatch').path.isfile.assert_called()
            patched.get('osPatch').path.isabs.assert_not_called()
            patched.get('getWorkDir').assert_not_called()
            patched.get('importlib').import_module.assert_not_called()

    def test_load_custom_ambiguous_module(self):
        customcommands._LOADED_MODULES['custom'] = StubbedModule()

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('yaml').safe_load.return_value = test_command
            patched.get('osPatch').path.isfile.return_value = True
            patched.get('osPatch').path.isabs.return_value = False
            patched.get('osPatch').path.dirname.return_value = workdir
            patched.get('osPatch').path.basename.return_value = 'custom.py'
            patched.get('getWorkDir').return_value = workdir
            patched.get('sysPatch').path = []

            with self.assertRaises(BuildConfigurationError) as e:
                customcommands.load_custom('custom-commands.yaml')

            self.assertTrue('conflicting' in e.exception.message)

            patched.get('yaml').safe_load.assert_called()
            patched.get('osPatch').path.isfile.assert_called()
            patched.get('osPatch').path.isabs.assert_called()
            patched.get('getWorkDir').assert_called()

            patched.get('importlib').import_module.return_value = customcommands._LOADED_MODULES['custom']
            customcommands.load_custom('custom-commands.yaml')  # shouldn't raise since they're the same modules

    def test_change_and_load_custom(self):
        patched: PatchedDependencies
        with self._patch() as patched, patch(f'{base_package}.load_custom') as custom:
            customcommands.change_and_load_custom(commands_path)

            patched.get('changeDir').assert_called_with(workdir)
            custom.assert_called_with('custom-commands.yaml')
            patched.get('changeBack').assert_called()

    def test_custom_command_path_validator(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('osPatch').path.isabs.return_value = True
            patched.get('osPatch').path.isfile.return_value = True

            self.assertIsNone(customcommands.custom_command_path_validator(commands_path))

            patched.get('osPatch').path.isabs.assert_called()
            patched.get('osPatch').path.isfile.assert_called()

            patched.get('osPatch').path.isabs.return_value = False
            patched.get('getWorkDir').return_value = workdir
            patched.get('osPatch').path.isfile.return_value = True

            self.assertIsNone(customcommands.custom_command_path_validator('commands.yaml'))

            patched.get('getWorkDir').assert_called()

            patched.get('osPatch').path.isabs.return_value = True
            patched.get('getWorkDir').return_value = workdir
            patched.get('osPatch').path.isfile.return_value = False

            self.assertTrue('is not a file' in customcommands.custom_command_path_validator(commands_path))
            self.assertTrue('is not a file' in customcommands.custom_command_path_validator('custom'))


if __name__ == '__main__':
    main()
