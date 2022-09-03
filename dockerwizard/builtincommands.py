"""
This module holds all the builtin commands
"""
import os

from .commands import AbstractCommand
from .errors import CommandError
from .process import Execution
from .cli import info, warn


class CopyCommand(AbstractCommand):
    """
    A command for copying files
    """
    def __init__(self):
        super().__init__('copy', 2)

    def _execute(self, args: list):
        import shutil
        from functools import partial

        if len(args) != 2:
            raise CommandError('The copy command needs 2 arguments')
        else:
            from_arg = args[0]
            to_arg = args[1]
            command = partial(shutil.copytree, from_arg, to_arg) if os.path.isdir(from_arg) \
                else partial(shutil.copy, from_arg, to_arg, follow_symlinks=True)

            command()

    def default_name(self):
        return 'Copy Files'


class ExecuteSystemCommand(AbstractCommand):
    """
    A command that executes a command on the host system shell
    """
    def __init__(self):
        super().__init__('execute-shell', 1, at_least=True)

    def _execute(self, args: list):
        if len(args) < 1:
            raise CommandError('The execute-shell command needs at least one argument')
        else:
            execution = Execution(args).execute()

            if not execution.is_healthy():
                raise CommandError(f'System command failed without stderr: {execution.stderr} and exit code:'
                                   f' {execution.exit_code}')
            else:
                if execution.stdout == '' and execution.stderr != '':
                    warn('Execution standard output is empty but stderr is not with 0 exit code. '
                         'This is confusing and should be avoided')
                    split = execution.stderr.splitlines()
                else:
                    split = execution.stdout.splitlines()

                joined = ' '.join(args)

                if len(split) == 0:
                    info(f'Command {joined} completed successfully with no output')
                else:
                    info(f'Command {joined} completed successfully with the following output')

                    for line in split:
                        info(f'\t{line}')

    def default_name(self):
        return 'Execute System Command'


class SetVariableCommand(AbstractCommand):
    """
    A command that allows you to set an environment variable
    """
    def __init__(self, secret: bool = False):
        self.secret = secret
        super().__init__('set-secret' if secret else 'set-variable', 2)

    def _execute(self, args: list):
        from os import environ
        self._do_set(args[0], args[1], environ)

    def _do_set(self, name: str, value: str, environ):
        if self.secret:
            info(f'Setting secret variable {name}')
        else:
            info(f'Setting variable {name} with value {value}')

        environ[name] = value

    def default_name(self):
        return 'Set Variable'


class SetVariablesCommand(AbstractCommand):
    """
    Allows the setting of multiple variables in one step by specifying a list of name=value pairs
    """
    def __init__(self):
        super().__init__('set-variables', 1, True)

    def _execute(self, args: list):
        from os import environ

        for arg in args:
            split = arg.split("=")

            if len(split) != 2:
                raise CommandError(f'Invalid variable format {arg}, format is key=value. Make sure key or value does '
                                   'not contain any = characters')
            else:
                name = split[0]
                value = split[1]

                if len(name.split(' ')) > 1:
                    raise CommandError('Names of variables cannot contain spaces')
                else:
                    environ[name] = value


class GitCloneCommand(AbstractCommand):
    """
    A command that allows a git repository to be cloned
    """
    def __init__(self):
        super().__init__('git-clone', 1, True, 2)

    def _execute(self, args: list):
        repo = args[0]
        name = args[1] if len(args) == 2 else None
        args = ['git', 'clone', repo]

        msg = f'Cloning Git repository {repo}'

        if name is not None:
            args.append(name)
            msg = f'{msg} into {name}'

        info(msg)

        result = Execution(args).execute()

        if result.exit_code != 0:
            stderr = result.stderr if result.stderr else result.stdout
            raise CommandError(f'Failed to perform git clone with error {stderr} and exit code {result.exit_code}')
        else:
            info(f'Git clone completed successfully')

    def default_name(self):
        return 'Git Clone'


def register_builtins():
    """
    Registers the builtin commands
    :return: None
    """
    for command in [CopyCommand, ExecuteSystemCommand, SetVariableCommand(False), SetVariableCommand(True),
                    SetVariablesCommand, GitCloneCommand()]:
        if isinstance(command, type):
            # has to be instantiated
            command()
