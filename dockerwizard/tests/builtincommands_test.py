"""
Tests for commands in the builtincommands module
"""
import contextlib
import os
import unittest
from unittest.mock import MagicMock, Mock, patch

from .testing import main, PatchedDependencies
from dockerwizard import builtincommands
from dockerwizard.builtincommands import CopyCommand, ExecuteSystemCommand, SetVariableCommand, \
    SetVariablesCommand, GitCloneCommand
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
            self.assertTrue(name in builtincommands.environ and builtincommands.environ[name] == value)
            patched.get('info').assert_called_with(f'Setting variable {name} with value {value}')

            self.command.secret = True
            self.command.execute(args)
            self.assertTrue(name in builtincommands.environ and builtincommands.environ[name] == value)
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
        self.assertTrue(name in builtincommands.environ and builtincommands.environ[name] == value)

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


class RegisterBuiltinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        types = {}
        types

    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'copy': f'{base_package}.CopyCommand',
            'execute': f'{base_package}.ExecuteSystemCommand',
            'setVar': f'{base_package}.SetVariableCommand',
            'setVars': f'{base_package}.SetVariablesCommand',
            'gitClone': f'{base_package}.GitCloneCommand'
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


if __name__ == '__main__':
    main()
