"""
This module tests the versioning module
"""
import contextlib
import unittest
from unittest.mock import Mock

from .testing import main, PatchedDependencies

from dockerwizard import versioning

base_package = 'dockerwizard.versioning'

python_version = '3.10'
system = 'Linux'
release = 'release'
processor = 'intel'
docker_version = '2.6'

docker_wizard_home = '/path/home'
docker_wizard_version = 'version'

versioning.DOCKER_WIZARD_CMD_NAME = 'docker-wizard'
versioning.VERSION = docker_wizard_version
versioning.DOCKER_WIZARD_HOME = docker_wizard_home


class VersioningTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'platform': f'{base_package}.platform',
            'info': f'{base_package}.info',
            'error': f'{base_package}.error',
            'execution': f'{base_package}.Execution'
        }) as patched:
            platform = patched.platform
            execution = patched.execution

            platform.python_version = Mock()
            platform.python_version.return_value = python_version
            platform.system = Mock()
            platform.system.return_value = system
            platform.release = Mock()
            platform.release.return_value = release
            platform.processor = Mock()
            platform.processor.return_value = processor

            execution.return_value = Mock()
            execution.return_value.execute = Mock()
            execution.return_value.execute.return_value = Mock()
            execution.return_value.execute.return_value.is_healthy = Mock()

            yield patched

    def test_healthy_version_action(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            docker_mock = patched.get('execution').return_value.execute.return_value
            docker_mock.is_healthy.return_value = True
            docker_mock.stdout = docker_version

            parser = Mock()
            namespace = Mock()
            values = Mock()

            execution = patched.get('execution')
            execution.return_value.execute.return_value.is_healthy.return_value = True

            versioning.VersionAction([''], '')(parser, namespace, values)

            info = patched.get('info')

            info.assert_any_call(f'{versioning.DOCKER_WIZARD_CMD_NAME} version {docker_wizard_version}')
            info.assert_any_call(f'DOCKER_WIZARD_HOME: {docker_wizard_home}')

            execution.assert_called_with(['docker', '--version'])
            execution.return_value.execute.assert_called()
            execution.return_value.execute.return_value.is_healthy.assert_called()

            info.assert_any_call(f'Docker Installation: {docker_version}')
            info.assert_any_call(f'Python Version: {python_version}, OS: {system}, Version: {release}, '
                                 f'Processor: {processor}')

            parser.exit.assert_called()

    def test_version_action_no_docker(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            docker_mock = patched.get('execution').return_value.execute.return_value
            docker_mock.is_healthy.return_value = False

            parser = Mock()
            namespace = Mock()
            values = Mock()

            execution = patched.get('execution')
            execution.return_value.execute.return_value.is_healthy.return_value = False

            versioning.VersionAction([''], '')(parser, namespace, values)

            patched.get('error').assert_called_with('Failed to retrieve Docker version '
                                                    'information (Docker may not be installed)')

            parser.exit.assert_called()


if __name__ == '__main__':
    main()
