"""
This module holds all the builtin commands
"""
import argparse
import os
import re
import shutil
from abc import ABC, abstractmethod

from . import commands
from .commands import AbstractCommand, CommandRegistry
from .docker import DockerClient
from .errors import CommandError
from .process import Execution, ExecutionResult
from .cli import info, warn
from .system import isWindows
from .const import DOCKER_WIZARD_BASH_PATH


class BuiltinCommand(ABC):
    """
    A base class for any builtin commands
    """
    @abstractmethod
    def print_help(self):
        """
        Print the help for this command
        """
        pass


class CopyCommand(AbstractCommand, BuiltinCommand):
    """
    A command for copying files
    """
    def __init__(self):
        super().__init__('copy', 2)

    @staticmethod
    def _call_copy_tree(from_arg, to_arg):
        shutil.copytree(from_arg, to_arg)

    @staticmethod
    def _call_copy(from_arg, to_arg):
        shutil.copy(from_arg, to_arg, follow_symlinks=True)

    def _execute(self, args: list):
        from_arg = args[0]
        to_arg = args[1]

        if os.path.isdir(from_arg):
            CopyCommand._call_copy_tree(from_arg, to_arg)
        else:
            CopyCommand._call_copy(from_arg, to_arg)

    def default_name(self):
        return 'Copy Files'

    def print_help(self):
        info(f'Command: {self.name}')
        info('Copies a source file to a destination relative to build directory')
        info('\tArguments: 2 arguments')
        info('\t\t1. Source file')
        info('\t\t2. Destination')


class _GenericOutputHandler:
    """
    A handler for common generic command output handling
    """
    @staticmethod
    def handle_output(execution: ExecutionResult, args: list, command_tag: str = 'System command'):
        """
        Handle the output of the provided execution with the args that were passed into the execution
        """
        if not execution.is_healthy():
            raise CommandError(f'{command_tag} failed with stderr: {execution.stderr} and exit code:'
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
                info(f'Command "{joined}" completed successfully with no output')
            else:
                info(f'Command "{joined}" completed successfully with the following output')

                for line in split:
                    info(f'\t{line}')


class ExecuteSystemCommand(AbstractCommand, BuiltinCommand):
    """
    A command that executes a command on the host system shell
    """
    def __init__(self):
        super().__init__('execute-shell', 1, at_least=True)

    def _resolve_bash(self, args: list):
        """
        If args[0] is bash and the OS is Windows, this method resolves it to Git Bash
        :return: true if it had to be resolved
        """
        first_arg = args[0]
        bash = 'bash'

        if first_arg == bash and isWindows():
            warn('Build is running on a Windows machine and the bash command is used in the execute-shell command. '
                 'Attempting to use bash emulator')

            warn('However, this should be avoided by using a Windows specific build file as the stability of the '
                 'build is not guaranteed')
            args[0] = DOCKER_WIZARD_BASH_PATH if DOCKER_WIZARD_BASH_PATH else bash

            return True

        return False

    def _execute(self, args: list):
        bash_resolved = self._resolve_bash(args)
        execution = Execution(args).execute()

        if bash_resolved and isWindows():
            # restore color after executing bash as it can reset the colors
            os.system('color')

        _GenericOutputHandler.handle_output(execution, args)

    def default_name(self):
        return 'Execute System Command'

    def print_help(self):
        info(f'Command: {self.name}')
        info('Executes a system command using the system shell (bash or cmd, e.g.')
        info('\tArguments: 1 or more arguments which are joined together and passed to the shell')
        info('\tIf the first argument is bash and the OS is windows, it will be resolved to a Bash Emulator')
        info('\tA path to a Bash emulator can be set using the DOCKER_WIZARD_BASH_PATH environment variable. If you '
             'have WSL installed, this is not required as bash is available with it')


class SetVariableCommand(AbstractCommand, BuiltinCommand):
    """
    A command that allows you to set an environment variable
    """
    def __init__(self, secret: bool = False):
        self.secret = secret
        super().__init__('set-secret' if secret else 'set-variable', 2)

    def _execute(self, args: list):
        self._do_set(args[0], args[1], os.environ)

    def _do_set(self, name: str, value: str, environs):
        if self.secret:
            info(f'Setting secret variable {name}')
        else:
            info(f'Setting variable {name} with value {value}')

        environs[name] = value

    def default_name(self):
        return 'Set Variable'

    def print_help(self):
        info(f'Command: {self.name}')
        if self.secret:
            info('Sets an environment variable with provided value, however does not log the value to console since '
                 'the value is treated as a secret')
        else:
            info('Sets an environment variable with provided value, logging it to the console')
        info('\tArguments: 2 arguments')
        info('\t\t1. Name of the variable')
        info('\t\t2. Value')


class SetVariablesCommand(AbstractCommand, BuiltinCommand):
    """
    Allows the setting of multiple variables in one step by specifying a list of name=value pairs
    """
    def __init__(self):
        super().__init__('set-variables', 1, True)

    def _execute(self, args: list):
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
                    os.environ[name] = value

    def print_help(self):
        info(f'Command: {self.name}')
        info('Provides the ability to set multiple environment variables by supplying key=value pairs')
        info('\tArguments: 1 or more arguments')


class GitCloneCommand(AbstractCommand, BuiltinCommand):
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

    def print_help(self):
        info(f'Command: {self.name}')
        info('Clones a git repository into the build directory')
        info('\tArguments: At least 1 argument, with optional 2nd argument')
        info('\t\t1. URL of git repository')
        info('\t\t2. Optional name of target directory to clone into')


class ScriptExecutorCommand(AbstractCommand, BuiltinCommand):
    """
    A command that can execute specified scripts
    """

    _EXTENSION_MAP = {
        'python': 'py',
        'groovy': 'groovy'
    }

    def __init__(self, interpreter: str):
        super().__init__(f'execute-{interpreter}', 1, at_least=True)
        self._interpreter = interpreter

    def _verify_script_passed(self, process_args: list):
        # verify that a script is passed into the command and now executing as interactive (e.g. just calling python)
        extension = ScriptExecutorCommand._EXTENSION_MAP.get(self._interpreter, self._interpreter)
        pattern = f'^(.+)\\.{extension}$'

        for arg in process_args:
            if re.match(pattern, arg):
                return

        # not found
        raise CommandError(f'The {self.name} command needs the name of a .{extension} script to be passed in')

    def _interpreter_capitalised(self):
        return f'{self._interpreter[:1].upper()}{self._interpreter[1:]}'

    def _execute(self, args: list):
        process_args = [self._interpreter]
        process_args.extend(args)
        self._verify_script_passed(process_args)

        execution = Execution(process_args).execute()

        _GenericOutputHandler.handle_output(execution, process_args, f'{self._interpreter_capitalised()} interpreter')

    def default_name(self):
        return f'Execute {self._interpreter_capitalised()} script'

    def print_help(self):
        info(f'Command: {self.name}')
        info(f'Executes a {self._interpreter} script')
        info(f'\tArguments: 1 or more arguments where one of the arguments must be a {self._interpreter} script file '
             f'ending in .{ScriptExecutorCommand._EXTENSION_MAP[self._interpreter]}. The rest of the arguments '
             f'can be flags passed to the {self._interpreter} interpreter')


class CreateContainerCommand(AbstractCommand, BuiltinCommand):
    """
    A command to create a container. Most useful as a post build step
    Args 0 is the name and 1 is the image (can have the command to run too in the same string).
    Extra args are arguments supported by docker build
    """
    def __init__(self):
        super().__init__('create-container', 2, at_least=True)

    def _execute(self, args: list):
        name = args[0]
        image = args[1]
        extra = args[2:] if len(args) > 2 else []
        execution = DockerClient.create_docker_container(image, name, extra)

        if execution.is_healthy():
            info(f'Container {name} created successfully from image {image} with hash {execution.stdout.strip()}')
        else:
            raise CommandError(f'Failed to create Docker container {name} from image {image} with error: '
                               f'{execution.stderr} and exit code: {execution.exit_code}')

    def default_name(self):
        return 'Create Docker Container'

    def print_help(self):
        info(f'Command: {self.name}')
        info('Create a Docker container. Always creates containers in detached mode (-d)')
        info('\tArguments: 2 or more arguments can be provided but the order must match the following')
        info('\t\t1. The name of the container to create')
        info('\t\t2. The tag/image of the container to run. Any command to execute in the created container can be'
             ' passed into this')
        info('\t\tOptional extra arguments like -p, --network etc. to pass to the docker run command')


class RunBuildCommand(AbstractCommand, BuiltinCommand):
    """
    A command that can run a build tool.
    USes named args with only one positional argument identifying the build tool to use
    """
    def __init__(self):
        super().__init__('run-build-tool', 1)
        self._tool_args = {}  # a dictionary of tool to list of required name args
        self._tool_args_getters = {}  # a dictionary to return args for the tool
        self._register_tools()

    def _register_tools(self):
        self._tool_args['maven'] = [('goals', True), ('arguments', False)]
        self._tool_args_getters['maven'] = RunBuildCommand._get_maven_args
        self._tool_args['npm'] = [('arguments', True)]
        self._tool_args_getters['npm'] = RunBuildCommand._get_npm_args

    def _validate_named_args(self, tool_name: str, named: dict):
        args_definition = self._tool_args[tool_name]

        for definition in args_definition:
            name = definition[0]
            required = False if len(definition) < 2 else definition[1]
            value = named.get(name)

            if not value and required:
                raise CommandError(f'Named argument {name} not provided')

    @staticmethod
    def _get_maven_args(named: dict) -> list:
        args = ['mvn']
        arguments = named.get('arguments')

        if arguments:
            args.extend(arguments)

        args.extend(named['goals'])

        return args

    @staticmethod
    def _get_npm_args(named: dict) -> list:
        args = ['npm']
        args.extend(named['arguments'])

        return args

    def _execute(self, args: list):
        tool = args[0]

        if tool not in self._tool_args and tool not in self._tool_args_getters:
            raise CommandError(f'Build tool {tool} not currently supported by the {self.name} command')
        else:
            named = self.build_context.current_step.named
            self._validate_named_args(tool, named)
            command_args = self._tool_args_getters[tool](named)
            execution = Execution(command_args).execute()
            _GenericOutputHandler.handle_output(execution, command_args, f'Run {tool} build')

    def default_name(self):
        return 'Run Build Tool'

    def print_help(self):
        info(f'Command: {self.name}')
        info('Run a supported build tool. Currently Maven (maven in args) and npm are supported')
        info('\tArguments: 1 positional argument identifying the build tool (maven | npm)')
        info('\tNamed Arguments:')
        info('\t\tmaven: Maven supports goals named arguments identifying a list of Maven goals (required). '
             'Also supports a list of arguments to pass to the maven command line')
        info('\t\tnpm: supports a list of arguments to pass to the nom command line')


def register_builtins():
    """
    Registers the builtin commands
    :return: None
    """
    # commands that are already instantiated like below are left out of below list
    SetVariableCommand(False)
    SetVariableCommand(True)
    ScriptExecutorCommand('groovy')
    ScriptExecutorCommand('python')

    for command in [CopyCommand, ExecuteSystemCommand, SetVariablesCommand, GitCloneCommand, CreateContainerCommand,
                    RunBuildCommand]:
        command()


def print_builtins_help():
    """
    Print the help of all builtin commands
    """
    commands.registry = CommandRegistry()
    register_builtins()
    info('The following are all the commands that are built-in to DockerWizard. The command tag, description and '
         'arguments information is offered')

    for value in commands.registry.commands.values():
        if isinstance(value, BuiltinCommand):
            value.print_help()
            info()


class BuiltinsHelpAction(argparse.Action):
    """
    An action to print builtin commands help and exit
    """
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print_builtins_help()
        parser.exit()
