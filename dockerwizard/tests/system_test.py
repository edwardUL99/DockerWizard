"""
Tests the system module
"""
import contextlib
import unittest
from unittest.mock import Mock

from .testing import main, PatchedDependencies
from dockerwizard import system


class SystemTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self, patch_docker_wizard_home: bool = False) -> PatchedDependencies:
        patch = {
            'system': 'platform.system',
            'register_builtins': 'dockerwizard.system.register_builtins',
            'os_environ_get': 'os.environ.get',
            'os_path_isdir': 'os.path.isdir'
        }

        if patch_docker_wizard_home:
            patch['docker_home'] = 'dockerwizard.system.docker_wizard_home'

        with PatchedDependencies(patch) as patched:
            yield patched

    def _test(self, func, platform_system, expected_return: bool):
        with self._patch() as patched:
            patched.get('system').return_value = platform_system
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

        with self._patch() as patched:
            patched.get('system').return_value = os_type.value
            init.initialise()
            callback.assert_called()

            os_type = system.OSTypes.ALL
            init = system.SystemInitialisation(os_type, callback)
            init.initialise()
            callback.assert_called()

    def test_docker_wizard_home(self):
        with self._patch() as patched:
            patched_get = patched.get('os_environ_get')
            patched_dir = patched.get('os_path_isdir')
            patched_get.return_value = 'docker-wizard-home'
            patched_dir.return_value = True
            self.assertEqual('docker-wizard-home', system.docker_wizard_home())
            patched_dir.return_value = False

            with self.assertRaises(SystemError):
                system.docker_wizard_home()

            patched_get.return_value = None

            with self.assertRaises(SystemError):
                system.docker_wizard_home()

    def test_system_init_registrations(self):
        old_initialisations = system._initialisations
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
        system._initialisations = old_initialisations

    def test_default_initialisations(self):
        with self._patch(True) as patched:
            system.initialise_system()

            patched.get('docker_home').assert_called()
            patched.get('register_builtins').assert_called()


if __name__ == '__main__':
    main()
