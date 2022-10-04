"""
Module to define all the commands supported by the framework
"""
from abc import ABC, abstractmethod

from .errors import CommandError


class Command(ABC):
    """
    The class defining the base for all commands
    """

    @abstractmethod
    def execute(self, args: list):
        """
        Executes the command with the args passed into it.
        Commands are in the form of name arg1 arg2 ... argsX
        Should throw errors.CommandError if the command fails to execute
        :param args: the list of args to the command , i.e. arg1, arg2 to argsX
        :return: None
        """
        pass

    def default_name(self):
        """
        Return the default name to use if a name is not provided in the build file
        :return: the default name
        """
        return '<unnamed>'


class CommandRegistry:
    """
    A registry of all commands
    """

    def __init__(self):
        self.commands = {}

    def register(self, name: str, command: Command):
        """
        Register the command to the given name
        :param name: the name of the command
        :param command: the command to register
        :return: None
        """
        self.commands[name] = command

    def get_command(self, name: str) -> Command:
        """
        Get the command with the given name or throw value error if not found
        :param name: the name of the command to retrieve
        :return: the retrieved command
        """
        command = self.commands.get(name)

        if command is None:
            raise ValueError(name)
        else:
            return command


registry = CommandRegistry()


class AbstractCommand(Command, ABC):
    """
    A base command that registers the command to the central command registry
    """

    def __init__(self, name: str, num_args_required: int, at_least: bool = False, max_num: int = -1):
        """
        Initialise the command with the name to register self with the registry and number of args required
        :param name: the name of the command
        :param num_args_required: the number of arguments this command requires
        :param at_least: if true, instead of a != check on args, a < num_args_required will be done (i.e. you need at
        lease num_args_required with an arbitrary number of them
        :param max_num: if at_least is true, max_num defines an upper bound, if -1 it is not checked (inclusive)
        """
        super().__init__()
        self.name = name
        self._num_args_required = num_args_required
        self._at_least = at_least
        self._max = max_num
        registry.register(name, self)

    def _at_least_max_predicate(self, args: list):
        """
        Predicate for arguments of at least X values
        """
        length = len(args)
        max_args = self._max != -1
        max_message = f' and maximum {self._max} arguments' if max_args else ''
        message = f'The {self.name} command requires at least {self._num_args_required} arguments{max_message}'

        return length < self._num_args_required or (max_args and length > self._max), message

    def _at_least_predicate(self, args: list):
        """
        A predicate for arguments with at least X values but max Y
        """
        message = f'The {self.name} command requires {self._num_args_required} arguments'

        return len(args) < self._num_args_required, message

    def _validate_num_args(self, args: list):
        """
        Validate the number of arguments passed in
        """
        if self._at_least:
            predicate = self._at_least_max_predicate
        else:
            predicate = self._at_least_predicate

        error, msg = predicate(args)

        if error:
            raise CommandError(msg)

    @property
    def build_context(self):
        """
        Returns the current build context. Should be called only in _execute since that is called during build time.
        init is called before a context is available
        """
        from .context import BuildContext  # prevent circular import
        return BuildContext.context()

    def execute(self, args: list):
        """
        Executes, validating the number of args passed in and then calls the _execute hook
        :param args: the args to validate
        :return: None
        """
        self._validate_num_args(args)

        try:
            self._execute(args)
        except Exception as e:
            if not isinstance(e, CommandError):
                raise CommandError(f'An unknown error was thrown executing command: {e}')
            else:
                raise e

    @abstractmethod
    def _execute(self, args: list):
        """
        Hook called by execute after arg validation
        """
        pass
