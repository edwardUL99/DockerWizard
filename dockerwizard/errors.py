"""
This file defines the classes representing errors in the project
"""


class BuildError(RuntimeError):
    """
    A base build error
    """
    pass


class BuildConfigurationError(BuildError):
    """
    An error related to a build configuration problem
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CommandError(BuildError):
    """
    An error related to a command problem
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BuildFailedError(BuildError):
    """
    A marker error to signal that the build has failed
    """
    pass
