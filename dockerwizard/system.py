"""
A module to encapsulate system related tasks
"""
import platform
import os
from typing import Callable, List
from enum import Enum


class OSTypes(Enum):
    """
    An enum representing the supported OS types
    """
    WINDOWS = 'windows'
    LINUX = 'linux'
    MAC = 'darwin'
    ALL = '*'  # An os type that means an init step should run regardless of os type


def _system():
    """
    Returns a normalized version of the platform system
    """
    return platform.system().lower()


def isWindows() -> bool:
    """
    Returns true if the OS is windows
    :return: true if OS is windows
    """
    return _system() == OSTypes.WINDOWS.value


def isLinux() -> bool:
    """
    Returns true if the OS is linux
    :return: true if OS is linux
    """
    return _system() == OSTypes.LINUX.value


def isMac() -> bool:
    """
    Returns true if the OS is mac
    :return: true if OS is mac
    """
    return _system() == OSTypes.MAC.value


class SystemInitialisation:
    """
    A class that represents a system initialisation that can occur depending on the OS
    """
    def __init__(self, os_type: OSTypes, callback: Callable):
        """
        Initialise the system initialisation object
        :param os_type: the type of the os to execute this system under. Pass in ALL to execute regardless of OS
        :param callback: the no-arg callback to perform initialisation
        """
        self.os_type = os_type.value
        self.callback = callback


    def initialise(self):
        """
        Perform the initialisation if the current OS matches the OS type
        :return: None
        """
        if self.os_type == OSTypes.ALL.value or _system() == self.os_type:
            self.callback()


def docker_wizard_home():
    """
    Validates the system DOCKER_WIZARD_HOME var exists and is a directory and returns the path
    :return: the DOCKER_WIZARD_HOME path
    """
    var = os.environ.get('DOCKER_WIZARD_HOME')

    if not var:
        raise SystemError('DOCKER_WIZARD_HOME needs to be set to the base of the project')
    elif not os.path.isdir(var):
        raise SystemError(f'DOCKER_WIZARD_HOME {var} is not a directory')

    return var


def register_builtins():
    """
    Registers builtin commands
    """
    # import here to avoid a circular import error
    from .builtincommands import register_builtins as _register
    _register()


# We use lambdas as they allow for easy testing. i.e. we can mock docker_wizard_home and register_builtins
# to assert they were called. If we passed the functions without lambdas and just a function reference, e.g.
# docker_wizard_home, even if we tried to patch docker_wizard_home to be a mock, the value passed into the init object
# is set to the un-mocked equivalent as the system module is imported
# With lambda, docker_wizard_home and register_builtins functions are resolved when the lambdas are called, and when
# this is in a test, these functions are mocks instead of the real ones
_initialisations: List[SystemInitialisation] = [
    SystemInitialisation(OSTypes.ALL, lambda: docker_wizard_home()),
    SystemInitialisation(OSTypes.ALL, lambda: register_builtins())
]


def register_system_initialisation(initialisation: SystemInitialisation):
    """
    Register the system initialisation step
    :param initialisation: the initialisation to execute on system startup
    :return: None
    """
    _initialisations.append(initialisation)


def initialise_system():
    """
    Initialise the system based on any registered system initialisations. This call should be performed before
    the system is ready to output anything to the user (i.e. make it the first call in entrypoint)
    :return: None
    """
    for init in _initialisations:
        init.initialise()
