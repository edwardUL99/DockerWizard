"""
This tests the builder module
"""
import contextlib
import unittest
from unittest.mock import Mock

import dockerwizard.errors
from dockerwizard.process import ExecutionResult
from .testing import main, PatchedDependencies, patch_os_path
from dockerwizard import builtincommands

old_register_builtins = builtincommands.register_builtins
builtincommands.register_builtins = Mock()

from dockerwizard import builder

old_temp_dir = builder.create_temp_directory
builder.create_temp_directory = Mock()

from dockerwizard import models

base_package = 'dockerwizard.builder'

image = 'test-build'

dockerfile = models.File()
dockerfile.path = 'Dockerfile'

library = 'files'

custom_commands = 'custom-commands.yaml'

file1 = models.File()
file1.path = 'hello-world.py'
file2 = models.File()
file2.path = '/test.txt'
file2.relative_to_library = False
files = [file1, file2]

step1 = models.BuildStep()
step1.name = 'test1'
step1.command = 'test1-command'
step1.arguments = ['arg', '1']
step2 = models.BuildStep()
step2.command = 'test2-command'
step2.arguments = ['arg', '2']
steps = [step1, step2]

step3 = models.BuildStep()
step3.name = 'test3'
step3.arguments = ['arg']
post_steps = [step3]

working_dir = '/path/workdir'


class StubTempDir:
    def __init__(self):
        self.name = working_dir
        setattr(self, 'cleanup', Mock())


class StubCommand:
    def __init__(self):
        self.executed = False
        self.args = []
        self.throw_error = False

    def execute(self, args):
        if self.throw_error:
            raise dockerwizard.errors.CommandError('error')

        self.executed = True
        self.args = args

    def default_name(self):
        return 'name'


class BuilderTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.builder = None
        self.test1_command = None
        self.test2_command = None
        self.test3_command = None

    @classmethod
    def tearDownClass(cls) -> None:
        builtincommands.register_builtins = old_register_builtins
        builder.create_temp_directory = old_temp_dir

    def setUp(self) -> None:
        config = models.DockerBuild()
        config.image = image
        config.dockerfile = dockerfile
        config.library = library
        config.custom_commands = custom_commands
        config.files = files
        config.steps = steps
        config.post_steps = post_steps

        builder.create_temp_directory.return_value = StubTempDir()
        self.builder = builder.Builder(config)

        self.test1_command = StubCommand()
        self.test2_command = StubCommand()
        self.test3_command = StubCommand()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'shutil': f'{base_package}.shutil',
            'osPatch': f'{base_package}.os',
            'changeDir': f'{base_package}.change_directory',
            'changeBack': f'{base_package}.change_back',
            'info': f'{base_package}.info',
            'error': f'{base_package}.error',
            'registry': f'{base_package}.registry',
            'changeLoadCustom': f'{base_package}.change_and_load_custom',
            'docker': f'{base_package}.DockerClient'
        }) as patched:
            patched.osPatch.path = patch_os_path()
            patched.shutil.copy = Mock()

            patched.docker.build_docker_image = Mock()

            def registry_side_effect(name):
                commands = {
                    step1.command: self.test1_command,
                    step2.command: self.test2_command,
                    step3.command: self.test3_command
                }

                command = commands.get(name)

                if not command:
                    raise ValueError

                return command

            patched.registry.get_command = Mock()
            patched.registry.get_command.side_effect = registry_side_effect

            yield patched

    def test_successful_build(self):
        docker_build = ExecutionResult(0, 'stdout', '')

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.docker.build_docker_image.return_value = docker_build

            return_val = self.builder.build()

            self.assertTrue(return_val)
            patched.shutil.copy.assert_any_call(f'{library}/Dockerfile', working_dir)
            patched.shutil.copy.assert_any_call(f'{library}/{file1.path}', working_dir)
            patched.shutil.copy.assert_any_call(f'{file2.path}', working_dir)
            patched.changeLoadCustom.assert_called_with(custom_commands)
            patched.changeDir.assert_any_call(working_dir)

            patched.changeDir.assert_any_call(working_dir, not_store=True)
            patched.registry.get_command.assert_any_call(step1.command)
            patched.registry.get_command.assert_any_call(step2.command)
            self.assertTrue(self.test1_command.executed)
            self.assertTrue(self.test2_command.executed)
            self.assertTrue(self.test3_command.executed)
            self.assertEqual(step1.arguments, self.test1_command.args)
            self.assertEqual(step2.arguments, self.test2_command.args)
            self.assertEqual(step3.arguments, self.test3_command.args)

            patched.docker.build_docker_image.assert_called_with(image)

            self.builder._working_directory.cleanup.assert_called()
            patched.changeBack.assert_called()

            # assert info messages
            patched.info.assert_any_call('Copying Dockerfile and required files to build directory')
            patched.info.assert_any_call('Copying Dockerfile Dockerfile from library to build directory')
            patched.info.assert_any_call(f'Copying file {file1.path} from library to build directory')
            patched.info.assert_any_call(f'Copying file {file2.path} to build directory')
            patched.info.assert_any_call('Dockerfile and required files successfully copied to build directory')
            patched.info.assert_any_call(f'Build specified custom commands file {custom_commands}. '
                                         'Loading commands into build')
            patched.info.assert_any_call('Changing working directory to build directory')
            patched.info.assert_any_call('Executing build steps')
            patched.info.assert_any_call(f'Executing build step 1 - {step1.name}')
            patched.info.assert_any_call('Executing build step 2 - name')
            patched.info.assert_any_call(f'Building Docker image with tag {image}')
            patched.info.assert_any_call(f'Docker image with tag {image} built successfully with the following output:')
            patched.info.assert_any_call(f'\tstdout')
            patched.info.assert_any_call('Executing post-build steps')
            patched.info.assert_any_call(f'Executing post-build step 1 - {step3.name}')
            patched.info.assert_any_call('Build finished, changing back to working directory')
            patched.info.assert_any_call('BUILD SUCCEEDED')

    def test_successful_build_without_custom_commands(self):
        docker_build = ExecutionResult(0, 'stdout', '')

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.docker.build_docker_image.return_value = docker_build
            self.builder.config.custom_commands = None

            return_val = self.builder.build()

            self.assertTrue(return_val)
            patched.changeLoadCustom.assert_not_called()

    def test_failed_build_unknown_command(self):
        docker_build = ExecutionResult(0, 'stdout', '')

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.docker.build_docker_image.return_value = docker_build
            unknown_step = models.BuildStep()
            unknown_step.command = 'unknown'
            self.builder.config.steps = [unknown_step]

            with self.assertRaises(dockerwizard.errors.BuildConfigurationError) as e:
                self.builder.build()

            self.assertTrue('Unknown command' in e.exception.message)

    def test_failed_build_command_error(self):
        docker_build = ExecutionResult(0, 'stdout', '')

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.docker.build_docker_image.return_value = docker_build
            self.test1_command.throw_error = True

            return_val = self.builder.build()

            self.assertFalse(return_val)
            patched.error.assert_any_call(f'Failed to execute build step 1 - {step1.name} with error: error')
            patched.error.assert_any_call('See logs to see why the build failed')
            patched.error.assert_any_call('BUILD FAILED')

    def test_failed_build_docker_error(self):
        failed_docker = ExecutionResult(1, '', 'error')
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.docker.build_docker_image.return_value = failed_docker

            return_val = self.builder.build()

            self.assertFalse(return_val)
            patched.error.assert_any_call('Failed to build Docker image with error error and '
                                          'exit code 1')
            patched.error.assert_any_call('See logs to see why the build failed')
            patched.error.assert_any_call('BUILD FAILED')


if __name__ == '__main__':
    main()
