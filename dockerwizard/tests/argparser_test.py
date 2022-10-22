"""
This tests the argparser module
"""
import sys
import unittest
from unittest.mock import MagicMock

from .testing import main
from dockerwizard import argparser


custom = 'custom-commands.yaml'
file = 'file.yaml'


class ArgparserTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)

    def test_flag_argument(self):
        parser = MagicMock()
        name = '-f'
        long_name = '--f'
        description = 'description'
        action = None
        required = True
        default = 'default'
        flag = argparser.FlagArgument(name=name, long_name=long_name, description=description, action=action,
                                      required=required, default=default)

        flag.add_to_parser(parser)

        parser.add_argument.assert_called_with(name, long_name, help=description, action=action,
                                               required=required, default=default)

    def test_positional_argument(self):
        parser = MagicMock()
        name = '-f'
        nargs = '*'
        description = 'description'
        action = None
        required = True
        default = 'default'
        flag = argparser.PositionalArgument(name=name, description=description, action=action,
                                            required=required, default=default, nargs=nargs)

        flag.add_to_parser(parser)

        parser.add_argument.assert_called_with(name, help=description, action=action,
                                               default=default, nargs=nargs)

    def test_all_args_provided(self):
        args = ['docker-wizard.py', '-c', custom, file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertEqual(custom, parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_all_args_long_names(self):
        args = ['docker-wizard.py', '--custom', custom, file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertEqual(custom, parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_only_file_provided(self):
        args = ['docker-wizard.py', file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertIsNone(parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_version_argument(self):
        args = ['docker-wizard.py', '-v']
        sys.argv = args

        with self.assertRaises(SystemExit) as e:
            argparser.parse()

        self.assertEqual(0, e.exception.code)

        args = ['docker-wizard.py', '--version']
        sys.argv = args

        with self.assertRaises(SystemExit) as e:
            argparser.parse()

        self.assertEqual(0, e.exception.code)

    def test_builtins_argument(self):
        args = ['docker-wizard.py', '-b']
        sys.argv = args

        with self.assertRaises(SystemExit) as e:
            argparser.parse()

        self.assertEqual(0, e.exception.code)

        args = ['docker-wizard.py', '--builtins']
        sys.argv = args

        with self.assertRaises(SystemExit) as e:
            argparser.parse()

        self.assertEqual(0, e.exception.code)


if __name__ == '__main__':
    main()
