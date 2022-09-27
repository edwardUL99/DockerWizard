"""
Tests the commands module
"""
import unittest

from .testing import main
from dockerwizard import commands
from dockerwizard.errors import CommandError


class StubCommand(commands.Command):
    def execute(self, args: list):
        pass


class CommandRegistryTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.registry = commands.CommandRegistry()

    def test_register(self):
        name = 'name'
        self.assertTrue(name not in self.registry.commands)
        self.registry.register(name, StubCommand())
        self.assertTrue(name in self.registry.commands)

    def test_get_command(self):
        name = 'name'
        command = StubCommand()
        self.registry.register(name, command)
        self.assertEqual(self.registry.get_command(name), command)

        with self.assertRaises(ValueError):
            self.registry.get_command('not-found')


class AbstractCommandStub(commands.AbstractCommand):
    def __init__(self, name: str, num_args_required: int, at_least: bool = False, max_num: int = -1,
                 throw_exception: bool = False):
        super().__init__(name, num_args_required, at_least, max_num)
        self.executed = False
        self.throw = throw_exception

    def execute(self, args: list):
        self.executed = False
        super().execute(args)

    def _execute(self, args: list):
        self.executed = True

        if self.throw:
            raise Exception('test-error')


class AbstractCommandTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)

    def test_fixed_args(self):
        num_args = 2
        name = 'test'
        command = AbstractCommandStub(name, num_args)

        self.assertFalse(command.executed)
        command.execute([1, 2])
        self.assertTrue(command.executed)

        with self.assertRaises(CommandError) as e:
            command.execute([])

        self.assertTrue('requires 2 arguments' in e.exception.message)

    def test_unbounded_args(self):
        num_args = 1
        at_least = True
        name = 'test'
        command = AbstractCommandStub(name, num_args, at_least)

        self.assertFalse(command.executed)
        command.execute([1, 2, 3])
        self.assertTrue(command.executed)

        with self.assertRaises(CommandError) as e:
            command.execute([])

        self.assertTrue('requires at least 1 arguments' in e.exception.message)
        self.assertFalse(command.executed)

    def test_at_least_max_arguments(self):
        num_args = 1
        at_least = True
        maximum = 2
        name = 'test'
        command = AbstractCommandStub(name, num_args, at_least, maximum)

        self.assertFalse(command.executed)
        command.execute([1, 2])
        self.assertTrue(command.executed)

        with self.assertRaises(CommandError) as e:
            command.execute([])

        self.assertTrue('requires at least 1 arguments' in e.exception.message)
        self.assertFalse(command.executed)

        with self.assertRaises(CommandError) as e:
            command.execute([1, 2, 3])

        self.assertTrue('requires at least 1 arguments and maximum 2' in e.exception.message)
        self.assertFalse(command.executed)

    def test_unknown_error_caught(self):
        num_args = 1
        name = 'test'
        command = AbstractCommandStub(name, num_args, throw_exception=True)

        with self.assertRaises(CommandError) as e:
            command.execute([1])

        self.assertTrue('An unknown error was thrown' in e.exception.message)


if __name__ == '__main__':
    main()
