"""
This tests the workdir package
"""
import contextlib
import unittest
from unittest.mock import Mock

from .testing import main, PatchedDependencies
from dockerwizard import workdir

base_package = 'dockerwizard.workdir'

working_dir = '/path/to/workdir'
new_dir = '/path/to/dir1'
new_dir1 = '/path/to/dir2'


class WorkdirTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self):
        with PatchedDependencies({
            'os': f'{base_package}.os',
            'tempfile': f'{base_package}.tempfile'
        }) as patched:
            patched.get('os').getcwd = Mock()

            yield patched

    def setUp(self) -> None:
        workdir._previous_directories.clear()

    def test_get_working_directory(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            os = patched.get('os')
            os.getcwd.return_value = working_dir

            self.assertEqual(working_dir, workdir.get_working_directory())
            os.getcwd.assert_called()

    def test_change_directory_and_change_back(self):
        current_dir = working_dir

        def side_effect(val: str):
            nonlocal current_dir
            current_dir = val

        patched: PatchedDependencies
        with self._patch() as patched:
            os = patched.get('os')
            os.chdir = Mock()
            os.chdir.side_effect = side_effect

            os.getcwd.return_value = current_dir
            workdir.change_directory(new_dir)
            self.assertEqual(current_dir, new_dir)

            os.getcwd.return_value = current_dir
            workdir.change_directory(new_dir1)
            self.assertEqual(current_dir, new_dir1)

            workdir.change_back()
            self.assertEqual(current_dir, new_dir)

            workdir.change_back()
            self.assertEqual(current_dir, working_dir)

            os.chdir.assert_called()
            os.getcwd.assert_called()

    def test_change_no_store(self):
        current_dir = working_dir

        def side_effect(val: str):
            nonlocal current_dir
            current_dir = val

        patched: PatchedDependencies
        with self._patch() as patched:
            os = patched.get('os')
            os.chdir = Mock()
            os.chdir.side_effect = side_effect

            os.getcwd.return_value = working_dir
            workdir.change_directory(new_dir, not_store=True)
            self.assertEqual(current_dir, new_dir)
            os.chdir.assert_called()
            os.chdir.reset_mock()

            workdir.change_back()
            self.assertEqual(current_dir, new_dir)
            os.chdir.assert_not_called()

    def test_create_temp_directory(self):
        temp_file = 'file'
        patched: PatchedDependencies
        with self._patch() as patched:
            tempfile = patched.get('tempfile')
            tempfile.TemporaryDirectory = Mock()
            tempfile.TemporaryDirectory.return_value = temp_file

            self.assertEqual(temp_file, workdir.create_temp_directory())

            tempfile.TemporaryDirectory.assert_called()

if __name__ == '__main__':
    main()
