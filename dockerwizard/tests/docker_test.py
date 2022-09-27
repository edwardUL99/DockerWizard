"""
This tests the docker module
"""
import contextlib
import unittest
from unittest.mock import Mock

from dockerwizard.process import ExecutionResult
from .testing import main, PatchedDependencies

from dockerwizard.docker import DockerClient


base_package = 'dockerwizard.docker'


class DockerClientTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.execute_mock = None

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'execution': f'{base_package}.Execution'
        }) as patched:
            self.execute_mock = Mock()
            patched.get('execution').return_value = Mock()
            patched.get('execution').return_value.execute = self.execute_mock

            yield patched

    def test_build_docker_image(self):
        tag = 'tag'
        workdir = 'workdir'

        with self._patch() as patched:
            result = ExecutionResult(0, 'stdout', '')
            self.execute_mock.return_value = result

            return_val = DockerClient.build_docker_image(tag)

            patched.get('execution').assert_any_call(['docker', 'build', '--tag', tag, '.'])
            self.assertEqual(return_val, result)

            return_val = DockerClient.build_docker_image(tag, workdir)

            patched.get('execution').assert_any_call(['docker', 'build', '--tag', tag, workdir])
            self.assertEqual(return_val, result)

    def test_create_docker_container(self):
        tag = 'tag'
        name = 'name'
        extra_args = ['-p', '8080:8080', '--network=host']

        with self._patch() as patched:
            result = ExecutionResult(0, 'stdout', '')
            self.execute_mock.return_value = result

            return_val = DockerClient.create_docker_container(tag, name, [])

            patched.get('execution').assert_any_call(['docker', 'run', '-d', '--name', name, tag])
            self.assertEqual(return_val, result)

            return_val = DockerClient.create_docker_container(tag, name, extra_args)

            patched.get('execution').assert_any_call(['docker', 'run', '-d', '--name', name, '-p', '8080:8080',
                                                      '--network=host', tag])
            self.assertEqual(return_val, result)


if __name__ == '__main__':
    main()
