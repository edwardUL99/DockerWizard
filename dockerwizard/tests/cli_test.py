"""
This tests the cli module
"""
import contextlib
import sys
import unittest
from unittest.mock import Mock

from .testing import main, PatchedDependencies

from dockerwizard import cli
from dockerwizard import system

test_info = 'info msg'
test_warn = 'warn msg'
test_error = 'error msg'

base_package = f'dockerwizard.cli'


def set_disabled(disabled: bool):
    if disabled:
        cli.disable()
    else:
        cli.enable()


class CliTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'osPatch': f'{base_package}.os',
            'printPatch': 'builtins.print'
        }) as patched:
            patched.osPatch.environ = Mock()
            patched.osPatch.environ.get = Mock()

            yield patched

    @classmethod
    def tearDownClass(cls) -> None:
        set_disabled(True)

    def setUp(self) -> None:
        set_disabled(False)

    def test_cli_print_enabled(self):
        set_disabled(False)

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('osPatch').environ.get.return_value = None

            print_info_msg = f'[{cli._GREEN}INFO{cli._RESET}] {test_info}'
            print_warn_msg = f'[{cli._YELLOW}WARNING{cli._RESET}] {test_warn}'
            print_error_msg = f'[{cli._RED}ERROR{cli._RESET}] {test_error}'

            print_patch = patched.get('printPatch')

            cli.info(test_info)
            cli.warn(test_warn)
            cli.error(test_error)

            print_patch.assert_any_call(print_info_msg)
            print_patch.assert_any_call(print_warn_msg)
            print_patch.assert_any_call(print_error_msg, file=sys.stderr)

    def test_cli_print_disabled(self):
        set_disabled(True)

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('osPatch').environ.get.return_value = None

            print_patch = patched.get('printPatch')

            cli.info(test_info)
            cli.warn(test_warn)
            cli.error(test_error)

            print_patch.assert_not_called()

            print_patch.reset_mock()

            set_disabled(False)
            patched.get('osPatch').environ.get.return_value = 'True'

            cli.info(test_info)
            cli.warn(test_warn)
            cli.error(test_error)

            print_patch.assert_not_called()


if __name__ == '__main__':
    main()
