"""
This tests the argparser module
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

from .testing import main
from dockerwizard import argparser


workdir = '/path/to/workdir'
default_workdir = '/path/to/default/workdir'
custom = 'custom-commands.yaml'
file = 'file.yaml'


class ArgparserTest(unittest.TestCase):
    def __init__(self, methodName):
        super().__init__(methodName)
        self.mocked_workdir = MagicMock()
        argparser.get_working_directory = self.mocked_workdir
        self.mocked_workdir.return_value = default_workdir

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
        args = ['docker-wizard.py', '-w', workdir, '-c', custom, file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertEqual(workdir, parsed.workdir)
        self.assertEqual(custom, parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_all_args_long_names(self):
        args = ['docker-wizard.py', '--workdir', workdir, '--custom', custom, file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertEqual(workdir, parsed.workdir)
        self.assertEqual(custom, parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_only_file_provided(self):
        args = ['docker-wizard.py', file]
        sys.argv = args
        parsed = argparser.parse()

        self.assertEqual(default_workdir, parsed.workdir)
        self.assertIsNone(parsed.custom)
        self.assertEqual(file, parsed.file)

    def test_missing_file_argument(self):
        args = ['docker-wizard.py']
        sys.argv = args

        with patch('sys.stderr'), self.assertRaises(SystemExit):
            argparser.parse()

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


if __name__ == '__main__':
    main()
