"""
This module represents build contexts
"""
from __future__ import annotations

from typing import Union

from .models import DockerBuild, BuildStep
from .errors import BuildContextError


class BuildContext:
    """
    Represents the context of the current build
    """

    _INSTANCE = None

    def __init__(self):
        self._config = None
        self._current_step = None

    @property
    def config(self) -> DockerBuild:
        """
        Gets the build config for this context
        """
        return self._config

    @config.setter
    def config(self, config):
        """
        Set the config object
        """
        self._config = config

    @property
    def current_step(self) -> BuildStep:
        """
        Returns the current build step being executed. If None, no step is being executed
        """
        return self._current_step

    @current_step.setter
    def current_step(self, current_step: Union[BuildStep, None]):
        """
        Sets the current build step
        """
        self._current_step = current_step

    @classmethod
    def context(cls) -> BuildContext:
        """
        Gets the current context.
        If not in a build context, an error is raised
        """
        if not cls._INSTANCE:
            raise BuildContextError()

        return cls._INSTANCE


def initialise():
    """
    Initialises the context
    """
    BuildContext._INSTANCE = BuildContext()

    return BuildContext.context()


def teardown():
    """
    Delete the build context
    """
    try:
        BuildContext._INSTANCE = None
    except BuildContextError:
        pass
