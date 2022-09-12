"""
Tests the system module
"""

import unittest
from unittest.mock import patch, Mock


from .testing import main
from dockerwizard import system


class SystemTest(unittest.TestCase):
    def _test(self, func, platform_system, expected_return: bool):
        with patch('platform.system') as patched:
            patched.return_value = platform_system
            return_val = func()
            self.assertEqual(expected_return, return_val)

    def test_isWindows(self):
        self._test(system.isWindows, 'Windows', True)
        self._test(system.isWindows, 'Linux', False)
        self._test(system.isWindows, 'Darwin', False)

    def test_isLinux(self):
        self._test(system.isLinux, 'Windows', False)
        self._test(system.isLinux, 'Linux', True)
        self._test(system.isLinux, 'Darwin', False)

    def test_isMac(self):
        self._test(system.isMac, 'Windows', False)
        self._test(system.isMac, 'Linux', False)
        self._test(system.isMac, 'Darwin', True)

    def test_system_initialisation(self):
        os_type = system.OSTypes.LINUX
        callback = Mock()

        init = system.SystemInitialisation(os_type, callback)

        with patch('platform.system') as patched:
            patched.return_value = os_type.value
            init.initialise()
            callback.assert_called()

            os_type = system.OSTypes.ALL
            init = system.SystemInitialisation(os_type, callback)
            init.initialise()
            callback.assert_called()

    def test_docker_wizard_home(self):
        with patch('os.environ.get') as patched, patch('os.path.isdir') as patchedDir:
            patched.return_value = 'docker-wizard-home'
            patchedDir.return_value = True
            self.assertEqual('docker-wizard-home', system.docker_wizard_home())
            patchedDir.return_value = False

            with self.assertRaises(SystemError):
                system.docker_wizard_home()

            patched.return_value = None

            with self.assertRaises(SystemError):
                system.docker_wizard_home()

    def test_system_init_registrations(self):
        system._initialisations = []
        initialized = False

        def callback():
            nonlocal initialized
            initialized = True

        test_init = system.SystemInitialisation(os_type=system.OSTypes.ALL, callback=callback)
        system.register_system_initialisation(test_init)
        index = None

        try:
            index = system._initialisations.index(test_init)
        except ValueError:
            pass

        self.assertIsNotNone(index)
        self.assertFalse(initialized)

        system.initialise_system()

        self.assertTrue(initialized)


if __name__ == '__main__':
    main()
