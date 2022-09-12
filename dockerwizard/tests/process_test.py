"""
This tests the process package
"""
import unittest
from unittest.mock import MagicMock, patch

from .testing import main
from dockerwizard import process


class ProcessTest(unittest.TestCase):
    def test_execution_result(self):
        healthy = process.ExecutionResult(0, '', '')
        self.assertTrue(healthy.is_healthy())

        unhealthy = process.ExecutionResult(1, '', '')
        self.assertFalse(unhealthy.is_healthy())

    def test_execution(self):
        mocked_popen = MagicMock()
        mocked_communicate = MagicMock()
        mocked_popen.communicate = mocked_communicate

        with patch('dockerwizard.process.Popen') as patched:
            patched.return_value = mocked_popen

            # test with string
            command = 'ls -l'
            process.Execution(command)
            patched.assert_any_call(command, stdout=process.PIPE, stderr=process.PIPE, text=True, shell=True)

            # test with list
            command = ['ls', '-l']
            process.Execution(command)
            patched.assert_any_call('ls -l', stdout=process.PIPE, stderr=process.PIPE, text=True, shell=True)

    def test_execution_execute(self):
        mocked_popen = MagicMock()
        mocked_communicate = MagicMock()
        mocked_popen.communicate = mocked_communicate

        with patch('dockerwizard.process.Popen') as patched:
            patched.return_value = mocked_popen
            execution = process.Execution(['ls', '-l'])
            mocked_communicate.return_value = ('ls -l output', '')
            mocked_popen.returncode = 0
            result = execution.execute()
            expected = process.ExecutionResult(0, 'ls -l output', '')

            self.assertEqual(result.exit_code, expected.exit_code)
            self.assertEqual(result.stdout, expected.stdout)
            self.assertEqual(result.stderr, expected.stderr)


if __name__ == '__main__':
    main()
