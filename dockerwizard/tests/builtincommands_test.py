"""
Tests for commands in the builtincommands module
"""
import argparse
import contextlib
import os
import unittest
from unittest.mock import Mock

from typing import Tuple

from dockerwizard.context import BuildContext
from dockerwizard.models import BuildStep
from dockerwizard.process import ExecutionResult
from .testing import main, PatchedDependencies
from dockerwizard import builtincommands, commands
from dockerwizard.builtincommands import CopyCommand, ExecuteSystemCommand, SetVariableCommand, \
    SetVariablesCommand, GitCloneCommand, ScriptExecutorCommand, CreateContainerCommand, RunBuildCommand
from dockerwizard.errors import CommandError


base_package = 'dockerwizard.builtincommands'


class CopyCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = CopyCommand()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'osDirMock': f'{base_package}.os.path.isdir',
            'shutilCopy': f'{base_package}.shutil.copy',
            'shutilCopyTree': f'{base_package}.shutil.copytree'
        }) as patched:
            yield patched

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'copy')

    def test_successful_execution(self):
        source = 'source'
        dest = 'destination'
        args = [source, dest]

        with self._patch() as patched:
            patched.get('osDirMock').return_value = False
            self.command.execute(args)
            patched.get('shutilCopy').assert_called_with(source, dest, follow_symlinks=True)

            patched.get('osDirMock').return_value = True
            self.command.execute(args)
            patched.get('shutilCopyTree').assert_called_with(source, dest)

    def test_invalid_args(self):
        args = ['source']

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('The copy command requires 2 arguments' in e.exception.message)


class ExecuteSystemCommandTest(unittest.TestCase):
    EXECUTION_MOCK = Mock()
    OLD_EXECUTION = None
    OLD_MODULE = None
    LAST_CALLED_ARGS = None

    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = ExecuteSystemCommand()

        self.executionMock = ExecuteSystemCommandTest.EXECUTION_MOCK

        class ExecutionStub:
            def __init__(self, args):
                ExecuteSystemCommandTest.LAST_CALLED_ARGS = args
                self.args = args
                self.executed = False

            def execute(self):
                self.executed = True

                return ExecuteSystemCommandTest.EXECUTION_MOCK

        ExecuteSystemCommandTest.OLD_MODULE = builtincommands
        ExecuteSystemCommandTest.OLD_EXECUTION = builtincommands.Execution
        builtincommands.Execution = ExecutionStub

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'osSystem': f'{base_package}.os.system',
            'isWindows': f'{base_package}.isWindows'
        }) as patched:
            yield patched

    @classmethod
    def tearDownClass(cls) -> None:
        ExecuteSystemCommandTest.OLD_MODULE.Execution = ExecuteSystemCommandTest.OLD_EXECUTION

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'execute-shell')

    def test_successful_execution(self):
        with self._patch():
            args = ['ls', '-l']
            self.executionMock.is_healthy.return_value = True
            self.executionMock.stdout = 'Test stdout'
            self.command.execute(args)

    def test_execution_failed(self):
        with self._patch():
            args = ['ls', '-l']
            self.executionMock.is_healthy.return_value = False
            self.executionMock.stderr = 'stderr'

            with self.assertRaises(CommandError) as e:
                self.command.execute(args)

            self.assertTrue('stderr: stderr' in e.exception.message)
            self.assertEqual(args, ExecuteSystemCommandTest.LAST_CALLED_ARGS)

    def test_invalid_args(self):
        args = []

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('The execute-shell command requires 1 arguments')

    def test_bash_resolution(self):
        from dockerwizard import const
        old_val = const.DOCKER_WIZARD_BASH_PATH
        builtincommands.DOCKER_WIZARD_BASH_PATH = 'test-bash-path'
        args = ['bash', 'script.sh']

        with self._patch() as patched:
            patched.get('isWindows').return_value = False
            self.executionMock.stdout = 'Test stdout'
            self.command.execute(args)
            self.assertEqual(args, ExecuteSystemCommandTest.LAST_CALLED_ARGS)

            patched.get('isWindows').return_value = True
            self.executionMock.stdout = 'Test stdout'
            self.command.execute(args)
            self.assertEqual(['test-bash-path', 'script.sh'], ExecuteSystemCommandTest.LAST_CALLED_ARGS)

        builtincommands.DOCKER_WIZARD_BASH_PATH = old_val


class SetVariableCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = SetVariableCommand()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'info': f'{base_package}.info'
        }) as patched:
            yield patched

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'set-variable')
        command = SetVariableCommand(secret=True)
        self.assertEqual(command.name, 'set-secret')

    def test_successful_execution(self):
        name = 'name'
        value = 'value'
        args = [name, value]
        old_environ = os.environ
        builtincommands.environ = {}

        with self._patch() as patched:
            self.command.execute(args)
            self.assertTrue(name in builtincommands.os.environ and builtincommands.os.environ[name] == value)
            patched.get('info').assert_called_with(f'Setting variable {name} with value {value}')

            self.command.secret = True
            self.command.execute(args)
            self.assertTrue(name in builtincommands.os.environ and builtincommands.os.environ[name] == value)
            patched.get('info').assert_called_with(f'Setting secret variable {name}')

            self.command.secret = False

        os.environ = old_environ

    def test_invalid_execution(self):
        args = ['name']

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('The set-variable command requires 2 arguments' in e.exception.message)


class SetVariablesCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = SetVariablesCommand()

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'set-variables')

    def test_successful_execution(self):
        name = 'name'
        value = 'value'
        composed = f'{name}={value}'
        args = [composed]

        old_environ = os.environ
        builtincommands.environ = {}

        self.command.execute(args)
        self.assertTrue(name in builtincommands.os.environ and builtincommands.os.environ[name] == value)

        os.environ = old_environ

    def test_invalid_execution(self):
        name = 'name spaces'
        value = 'value'
        composed = f'{name}={value}'
        args = [composed]

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('Names of variables cannot contain spaces' in e.exception.message)

        composed = f'{name}{value}'
        args = [composed]

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('format is key=value' in e.exception.message)

        args = []
        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('The set-variables command requires at least 1 arguments' in e.exception.message)


class StubbedExecution:
    def __init__(self, mock):
        self.mock = mock

    def execute(self):
        return self.mock


class GitCloneCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = GitCloneCommand()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'execution': f'{base_package}.Execution',
            'info': f'{base_package}.info'
        }) as patched:
            yield patched

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'git-clone')

    def test_successful_execution(self):
        repo = 'test-repo'
        args = [repo]

        with self._patch() as patched:
            mocked_result = Mock()
            patched.get('execution').return_value = StubbedExecution(mocked_result)

            mocked_result.exit_code = 0

            self.command.execute(args)
            patched.get('info').assert_any_call(f'Cloning Git repository {repo}')
            patched.get('info').assert_any_call(f'Git clone completed successfully')
            patched.get('execution').assert_called_with(['git', 'clone', repo])

            args = [repo, 'dest']

            patched.get('execution').return_value = StubbedExecution(mocked_result)

            mocked_result.exit_code = 0

            self.command.execute(args)
            patched.get('info').assert_any_call(f'Cloning Git repository {repo} into dest')
            patched.get('info').assert_any_call(f'Git clone completed successfully')
            patched.get('execution').assert_called_with(['git', 'clone', repo, 'dest'])

    def test_failed_git_clone(self):
        repo = 'test-repo'
        args = [repo]

        with self._patch() as patched:
            mocked_result = Mock()
            patched.get('execution').return_value = StubbedExecution(mocked_result)
            mocked_result.exit_code = 1
            mocked_result.stderr = 'stderr'

            with self.assertRaises(CommandError) as e:
                self.command.execute(args)

            self.assertTrue('git clone with error stderr' in e.exception.message)

    def test_invalid_execution(self):
        args = []
        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('The git-clone command requires at least 1 arguments' in e.exception.message)


class ScriptExecutorCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = ScriptExecutorCommand('python')

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'execution': f'{base_package}.Execution',
            'info': f'{base_package}.info'
        }) as patched:
            execution_returned = Mock()
            execution_returned.execute = Mock()
            patched.get('execution').return_value = execution_returned

            yield patched

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'execute-python')

    def test_successful_execution(self):
        args = ['script.py']
        return_val = ExecutionResult(0, 'success', '')

        with self._patch() as patched:
            patched.get('execution').return_value.execute.return_value = return_val

            self.command.execute(args)

            patched.get('execution').assert_called_with(['python', args[0]])
            patched.get('execution').return_value.execute.assert_called()
            patched.get('info').assert_any_call('Command "python script.py" completed successfully with the following '
                                                'output')
            patched.get('info').assert_any_call('\tsuccess')

    def test_failed_execution(self):
        args = ['script.py']
        return_val = ExecutionResult(1, '', 'failed')

        with self._patch() as patched:
            patched.get('execution').return_value.execute.return_value = return_val

            with self.assertRaises(CommandError) as e:
                self.command.execute(args)

            self.assertTrue('Python interpreter failed with stderr: failed and exit code: 1' in e.exception.message)

            patched.get('execution').assert_called_with(['python', args[0]])
            patched.get('execution').return_value.execute.assert_called()

    def test_invalid_args(self):
        args = []

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('requires at least 1 arguments' in e.exception.message)

    def test_no_script_provided(self):
        args = ['-u']

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('needs the name of a .py script' in e.exception.message)


class CreateContainerCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = CreateContainerCommand()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'docker': f'{base_package}.DockerClient',
            'info': f'{base_package}.info'
        }) as patched:
            patched.get('docker').create_docker_container = Mock()
            yield patched

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'create-container')

    def test_successful_execution_minimal_args(self):
        args = ['test-container', 'test-image']
        result = ExecutionResult(0, 'hash', '')

        with self._patch() as patched:
            patched.get('docker').create_docker_container.return_value = result
            self.command.execute(args)

            patched.get('docker').create_docker_container.assert_called_with('test-image', 'test-container', [])
            patched.get('info').assert_called_with('Container test-container created successfully from image '
                                                   'test-image with hash hash')

    def test_successful_execution_supplemental_args(self):
        args = ['test-container', 'test-image', '-p', '8080:8080', '--network=host']
        result = ExecutionResult(0, 'hash', '')

        with self._patch() as patched:
            patched.get('docker').create_docker_container.return_value = result
            self.command.execute(args)

            patched.get('docker').create_docker_container.assert_called_with('test-image', 'test-container',
                                                                             ['-p', '8080:8080', '--network=host'])
            patched.get('info').assert_called_with('Container test-container created successfully from image '
                                                   'test-image with hash hash')

    def test_failed_execution(self):
        args = ['test-container', 'test-image']
        result = ExecutionResult(1, '', 'failed')

        with self._patch() as patched:
            patched.get('docker').create_docker_container.return_value = result

            with self.assertRaises(CommandError) as e:
                self.command.execute(args)

            self.assertTrue('Failed to create Docker container test-container from image '
                            'test-image with error: failed and exit code: 1' == e.exception.message)
            patched.get('docker').create_docker_container.assert_called_with('test-image', 'test-container', [])

    def test_invalid_args(self):
        args = []

        with self.assertRaises(CommandError) as e:
            self.command.execute(args)

        self.assertTrue('requires at least 2 arguments' in e.exception.message)


class RunBuildCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.command = RunBuildCommand()

    @contextlib.contextmanager
    def _patch(self) -> Tuple[PatchedDependencies, Mock]:
        with PatchedDependencies({
            'execution': f'{base_package}.Execution',
            'outputHandler': f'{base_package}._GenericOutputHandler'  # already tested previously so mock here
        }) as patched, unittest.mock.patch(f'{base_package}.AbstractCommand.build_context',
                                           new_callable=unittest.mock.PropertyMock) as property_mock:
            execution_returned = Mock()
            execution_returned.execute = Mock()
            patched.get('execution').return_value = execution_returned

            yield patched, property_mock

    @staticmethod
    def _create_build_step(named: dict):
        step = BuildStep()
        step.named = named

        return step

    @staticmethod
    def _mock_build_context():
        return BuildContext()

    def test_initialisation(self):
        self.assertEqual(self.command.name, 'run-build-tool')

    def test_mvn_build(self):
        named = {
            'goals': ['clean', 'install']
        }

        with self._patch() as val:
            patched = val[0]
            property_mock = val[1]
            context = RunBuildCommandTest._mock_build_context()
            context.current_step = RunBuildCommandTest._create_build_step(named)
            property_mock.return_value = context
            test_execution = ExecutionResult(0, '', '')
            patched.get('execution').return_value.execute.return_value = test_execution

            self.command.execute(['maven'])
            patched.get('execution').assert_any_call(['mvn', 'clean', 'install'])

            named['arguments'] = ['-DskipTests']

            self.command.execute(['maven'])
            patched.get('execution').assert_any_call(['mvn', '-DskipTests', 'clean', 'install'])

            named['goals'] = None
            with self.assertRaises(CommandError) as e:
                self.command.execute(['maven'])

            self.assertTrue('Named argument goals not provided' in e.exception.message)

    def test_npm_build(self):
        named = {
            'arguments': ['install']
        }

        with self._patch() as val:
            patched = val[0]
            property_mock = val[1]
            context = RunBuildCommandTest._mock_build_context()
            context.current_step = RunBuildCommandTest._create_build_step(named)
            property_mock.return_value = context
            test_execution = ExecutionResult(0, '', '')
            patched.get('execution').return_value.execute.return_value = test_execution

            self.command.execute(['npm'])
            patched.get('execution').assert_any_call(['npm', 'install'])

    def test_build_unknown_tool(self):
        with self.assertRaises(CommandError) as e:
            self.command.execute(['unknown'])

        self.assertTrue('Build tool unknown not currently supported' in e.exception.message)

    def test_invalid_arguments(self):
        with self.assertRaises(CommandError) as e:
            self.command.execute([])

        self.assertTrue('requires 1 arguments' in e.exception.message)


class RegisterBuiltinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        commands.registry = commands.CommandRegistry()

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'copy': f'{base_package}.CopyCommand',
            'execute': f'{base_package}.ExecuteSystemCommand',
            'setVar': f'{base_package}.SetVariableCommand',
            'setVars': f'{base_package}.SetVariablesCommand',
            'gitClone': f'{base_package}.GitCloneCommand',
            'scriptExecutor': f'{base_package}.ScriptExecutorCommand',
            'createContainer': f'{base_package}.CreateContainerCommand'
        }) as patched:
            yield patched

    def test_register_builtins(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            builtincommands.register_builtins()

            patched.copy.assert_called()
            patched.execute.assert_called()
            patched.setVar.assert_any_call(True)
            patched.setVar.assert_any_call(False)
            patched.setVars.assert_called()
            patched.gitClone.assert_called()
            patched.scriptExecutor.assert_any_call('python')
            patched.scriptExecutor.assert_any_call('groovy')
            patched.createContainer.assert_called()


class BuiltinHelpTest(unittest.TestCase):
    """
    A very simple test case just to verify that all builtin commands implement the print_help method without throwing errors
    """
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'info': f'{base_package}.info',
            'print_help': f'{base_package}.print_builtins_help'
        }) as patched:
            yield patched

    def test_commands_help(self):
        # save function ref before patching
        builtins_help = builtincommands.print_builtins_help

        with self._patch() as patched:
            old_commands_registry = commands.registry
            builtins_help()
            commands_registry = commands.registry

            self.assertNotEqual(old_commands_registry, commands_registry)
            patched.get('info').assert_called()

    def test_builtins_help_action(self):
        parser = Mock()
        parser.exit = Mock()
        action = builtincommands.BuiltinsHelpAction([''], '')

        with self._patch() as patched:
            action(parser, argparse.Namespace(), [''])
            patched.get('print_help').assert_called()
            parser.exit.assert_called()


if __name__ == '__main__':
    main()
