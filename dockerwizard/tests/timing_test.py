"""
Tests the timing module
"""
import unittest
from unittest.mock import Mock
import contextlib

from .testing import main, PatchedDependencies

from dockerwizard import timing


base_package = 'dockerwizard.timing'


class TimingTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        with PatchedDependencies({
            'time': f'{base_package}.time',
            'timedelta': f'{base_package}.timedelta',
        }) as patched:
            patched.get('time').time = Mock()
            yield patched

    def setUp(self) -> None:
        timing._start_time = 0
        timing._end_time = 0

    def test_start(self):
        with self._patch() as patched:
            return_value = 1
            patched.get('time').time.return_value = return_value

            timing.start()

            self.assertEqual(return_value, timing._start_time)
            patched.get('time').time.assert_called()

    def test_end(self):
        with self._patch() as patched:
            return_value = 1
            patched.get('time').time.return_value = return_value

            timing.end()

            self.assertEqual(return_value, timing._end_time)
            patched.get('time').time.assert_called()

    def test_get_duration(self):
        with self._patch() as patched:
            return_value = 1
            patched.get('time').time.return_value = return_value
            timing.start()
            return_value = 10
            patched.get('time').time.return_value = return_value
            timing.end()

            patched.get('timedelta').return_value = '0:10:12.12345'

            duration = timing.get_duration()

            self.assertEqual(duration, '0H:10M:12S')
            patched.get('timedelta').assert_called_with(seconds=9)
            patched.get('timedelta').reset_mock()
            patched.get('timedelta').return_value = '0:10:12'

            duration = timing.get_duration()

            self.assertEqual(duration, '0H:10M:12S')
            patched.get('timedelta').assert_called_with(seconds=9)
            patched.get('timedelta').reset_mock()


if __name__ == '__main__':
    main()
