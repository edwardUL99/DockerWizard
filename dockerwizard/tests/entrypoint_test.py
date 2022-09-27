"""
This tests the entrypoint module
"""
import argparse
import contextlib
import unittest
from unittest.mock import MagicMock

from dockerwizard.const import CUSTOM_COMMANDS
from .testing import main, PatchedDependencies, patch_os_path, test_join
from dockerwizard import entrypoint
from dockerwizard.models import DockerBuild

base_package = 'dockerwizard.entrypoint'
wizard_home = '/home/to/docker_wizard'
workdir = wizard_home


class EntrypointTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'initPatch': f'{base_package}.initialise_system',
            'changeDir': f'{base_package}.change_directory',
            'argParse': f'{base_package}.parse',
            'changeBack': f'{base_package}.change_back',
            'workingDirectory': f'{base_package}.get_working_directory',
            'buildParser': f'{base_package}.get_build_parser',
            'builder': f'{base_package}.Builder',
            'wizardHome': f'{base_package}.docker_wizard_home',
            'osPatched': f'{base_package}.os',
            'loadCustom': f'{base_package}.load_custom',
            'customPathValidator': f'{base_package}.custom_command_path_validator'
        }) as patched:
            patched.osPatched.path = patch_os_path()

            yield patched

    @staticmethod
    def _default_patch_values(patched):
        patched.get('wizardHome').return_value = wizard_home
        patched.get('buildParser').return_value = MagicMock()
        patched.get('builder').return_value = MagicMock()
        patched.get('customPathValidator').return_value = None
        patched.get('workingDirectory').return_value = workdir
        patched.get('buildParser').return_value.parse.return_value = DockerBuild()

    @staticmethod
    def is_file_side_effect(args: dict):
        def is_file(path) -> bool:
            if path in args:
                return args[path]
            else:
                return False

        return is_file

    def test_entrypoint_no_custom(self):
        args = argparse.Namespace()
        args.custom = None
        args.workdir = workdir
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('osPatched').path.isfile.side_effect = EntrypointTest.is_file_side_effect({
                f'{args.workdir}/{CUSTOM_COMMANDS}': False,
                f'{wizard_home}/{CUSTOM_COMMANDS}': False,
                f'{workdir}/{args.file}': True
            })

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isfile.return_value = True
            patched.get('builder').return_value.build.return_value = True
            patched.get('customPathValidator').return_value = 'not a file'

            entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('loadCustom').assert_not_called()
            patched.get('buildParser').return_value.parse.assert_called_with(test_join(workdir, 'file.yaml'))
            patched.get('builder').return_value.build.assert_called()

    def test_entrypoint_custom(self):
        args = argparse.Namespace()
        args.custom = 'commands.yaml'
        args.workdir = workdir
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isfile.return_value = True
            patched.get('osPatched').path.isabs.return_value = False
            patched.get('builder').return_value.build.return_value = True

            entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('loadCustom').assert_called_with('commands.yaml')
            patched.get('buildParser').return_value.parse.assert_called_with(test_join(workdir, 'file.yaml'))
            patched.get('builder').return_value.build.assert_called()

    def test_entrypoint_custom_not_found(self):
        args = argparse.Namespace()
        args.custom = 'commands.yaml'
        args.workdir = workdir
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('osPatched').path.isfile.side_effect = EntrypointTest.is_file_side_effect({
                args.custom: False,
                f'{workdir}/{args.file}': True
            })

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isabs.return_value = False

            with self.assertRaises(SystemExit):
                entrypoint.main()

            patched.get('initPatch').assert_called()

    def test_entrypoint_custom_in_workdir(self):
        args = argparse.Namespace()
        args.custom = None
        args.workdir = f'{workdir}/test'
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('workingDirectory').return_value = args.workdir

            patched.get('osPatched').path.isfile.side_effect = EntrypointTest.is_file_side_effect({
                f'{args.workdir}/{CUSTOM_COMMANDS}': True,
                f'{workdir}/{CUSTOM_COMMANDS}': False,
                f'{args.workdir}/{args.file}': True
            })

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isabs.return_value = False
            patched.get('builder').return_value.build.return_value = True

            entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('loadCustom').assert_called_with('custom-commands.yaml')
            patched.get('buildParser').return_value.parse.assert_called_with(test_join(args.workdir, 'file.yaml'))
            patched.get('builder').return_value.build.assert_called()

    def test_entrypoint_build_file_not_found(self):
        args = argparse.Namespace()
        args.custom = None
        args.workdir = workdir
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('argParse').return_value = args
            patched.get('builder').return_value.build.return_value = True
            patched.get('osPatched').path.isfile.return_value = False

            with self.assertRaises(SystemExit):
                entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('buildParser').assert_not_called()
            patched.get('buildParser').return_value.assert_not_called()
            patched.get('builder').return_value.assert_not_called()

    def test_entrypoint_workdir_not_found(self):
        args = argparse.Namespace()
        args.custom = None
        args.workdir = f'{workdir}/not-found'
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isfile.return_value = True
            patched.get('osPatched').path.isdir.return_value = False

            with self.assertRaises(SystemExit):
                entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('buildParser').assert_not_called()
            patched.get('buildParser').return_value.assert_not_called()
            patched.get('builder').return_value.assert_not_called()

    def test_entrypoint_build_failed(self):
        args = argparse.Namespace()
        args.custom = None
        args.workdir = workdir
        args.file = 'file.yaml'

        patched: PatchedDependencies
        with self._patch() as patched:
            EntrypointTest._default_patch_values(patched)

            patched.get('argParse').return_value = args
            patched.get('osPatched').path.isfile.return_value = True
            patched.get('builder').return_value.build.return_value = False
            patched.get('customPathValidator').return_value = None

            with self.assertRaises(SystemExit):
                entrypoint.main()

            patched.get('initPatch').assert_called()
            patched.get('buildParser').return_value.parse.assert_called_with(test_join(workdir, 'file.yaml'))
            patched.get('builder').return_value.build.assert_called()


if __name__ == '__main__':
    main()
