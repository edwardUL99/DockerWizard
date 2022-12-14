"""
This file exports models that are used throughout the dockerwizard module
"""
import os.path
from abc import ABC, abstractmethod
from typing import Callable, List

from .errors import BuildConfigurationError
from .workdir import get_working_directory
from .customcommands import custom_command_path_validator


class BuildFileData:
    """
    A class that allows abstract access to properties in a build file
    """
    def __init__(self, data: dict):
        self._data = data

    @property
    def data(self) -> dict:
        """
        Returns raw data dictionary as a copy
        """
        return self._data.copy()

    def get_property(self, key: str):
        return self._data.get(key)

    def set_properties(self, setters: List, target):
        """
        Call process on all the PropertySetters in the given list
        :param setters: the list of PropertySetters to apply to this data
        :param target: the target build file object
        :return: None
        """
        for setter in setters:
            setter.process(self, target)


class BuildFileObject(ABC):
    """
    A base object representing an object nested in a build file
    """
    def __init__(self, tag_name: str = None):
        """
        Create a base object with the given tag_name in the file
        Subclasses should initialise all the valid properties here
        :param tag_name: the name of the tag if a nested object
        """
        self.tag_name = tag_name

    @abstractmethod
    def initialise(self, data: BuildFileData):
        """
        Initialise the build file object from the data read from the build file
        :param data: the data dictionary from the build file
        :return: should return instance of self
        """
        pass

    def set_property(self, name: str, value):
        """
        Sets the property identified by the given name with the given value. If the subclass doesn't have the property
        a ValueError will be thrown
        :param name: the name of the property
        :param value: the value to set
        :return: None
        """
        if hasattr(self, name):
            if value is not None:
                setattr(self, name, value)
        else:
            raise ValueError(f'Property {name} is not valid')


class PropertySetter:
    """
    A class that pulls a property from build data and then passes it into the provided lambda function
    """
    def __init__(self, name: str, required: bool = False, validate: Callable = None, on_error: Callable = None):
        """
        Initialise a property processor
        :param name: the name of the property to pull
        :param required: if required and property is not found, the error message will be passed into on_error
        :param validate: a validate function to validate the property and return an error message to pass into on_error
        if not valid
        :param on_error: a callback when the property is not found and it is required or validate fails
        """
        self.name = name
        self.required = required
        self.validate = validate
        self.on_error = on_error

    def _error(self, e):
        """
        Execute the error handler if it is not none
        :param e: the error to pass into the callback
        :return: None
        """
        if self.on_error is not None:
            self.on_error(e)

    def process(self, data: BuildFileData, target: BuildFileObject):
        value = data.get_property(self.name)

        if self.required and not value:
            self._error(f'{self.name} not found')
        else:
            if value is not None:
                validate_error = self.validate(value) if self.validate is not None else None

                if validate_error is not None:
                    self._error(validate_error)
                else:
                    target.set_property(self.name, value)


def throw_property_error(e: str):
    """
    Throws the error e as a BuildConfigurationError
    :param e: the error to throw
    :return: None
    """
    raise BuildConfigurationError(e)


class BaseFileObject(BuildFileObject):
    """
    A base build file object which provides the recommended implementation of initialise which returns self
    """
    def __init__(self, tag_name: str = None):
        super().__init__(tag_name=tag_name)

    def initialise(self, data: BuildFileData):
        """
        Recommended initialisation method that calls the do_initialise hook and returns self
        :param data: the data to initialise with
        :return: self
        """
        self.do_initialise(data)

        return self

    @abstractmethod
    def do_initialise(self, data: BuildFileData):
        """
        The hook that initialise calls upon
        :param data: the data to initialise with
        :return: None
        """
        pass


class File(BaseFileObject):
    """
    A file required by the build step
    """
    def __init__(self):
        super().__init__()
        self.path: str = ''
        self.relative_to_library: bool = True

    def do_initialise(self, data: BuildFileData):
        setters = [
            PropertySetter('path', required=True, on_error=throw_property_error),
            PropertySetter('relative_to_library')
        ]

        data.set_properties(setters, self)


class Files(BaseFileObject):
    """
    The list of files needed by a build step
    """
    def __init__(self):
        super().__init__('files')
        self.files: List[File] = []

    def do_initialise(self, data: BuildFileData):
        files_list = data.get_property(self.tag_name)

        if files_list is None:
            raise BuildConfigurationError('Attempted to initialise files but files does not exist in BuildFileData')

        self.files = [File().initialise(f) for f in files_list]


class BuildStep(BaseFileObject):
    """
    Represents the build step object
    """
    def __init__(self):
        super().__init__()
        self.name = None
        self.command: str = ''
        self.arguments: list = []
        # additional named properties rather than positional arguments. Not directly passed into command execute
        # but can be accessed in build context current_step
        # not converted to BuildFileData, kept as simple dict
        self.named: dict = {}

    def do_initialise(self, data: BuildFileData):
        setters = [
            PropertySetter('name', on_error=throw_property_error),
            PropertySetter('command', required=True, on_error=throw_property_error),
            PropertySetter('arguments', on_error=throw_property_error),
            PropertySetter('named', on_error=throw_property_error)
        ]

        data.set_properties(setters, self)

        self.named = self.named.data if isinstance(self.named, BuildFileData) else self.named


class BuildSteps(BaseFileObject):
    """
    Represents the build steps of a build file
    """
    def __init__(self, post_build: bool = False):
        super().__init__('steps' if not post_build else 'post')
        self.steps: List[BuildStep] = []
        self._post = post_build

    def do_initialise(self, data: BuildFileData):
        key = 'steps' if not self._post else 'post'
        steps_list = data.get_property('steps' if not self._post else 'post')

        if steps_list is None:
            raise BuildConfigurationError(f'Attempted to initialise {key} but {key} does not exist in BuildFileData')

        self.steps = [BuildStep().initialise(s) for s in steps_list]


class DockerBuild(BaseFileObject):
    """
    Represents the whole docker build object
    """
    def __init__(self):
        super().__init__('build')
        self.image: str = ''
        self.dockerfile: File = File()
        self.library: str = ''
        self.custom_commands: str = ''
        self.files: List[File] = []
        self.steps: List[BuildStep] = []
        self.post_steps: List[BuildStep] = []

    def _convert_custom_commands(self):
        if self.custom_commands:
            if not os.path.isabs(self.custom_commands):
                self.custom_commands = os.path.join(get_working_directory(), self.custom_commands)

    def do_initialise(self, data: BuildFileData):
        def validate_file_library(path: str):
            if not os.path.isdir(path):
                return f'{path} is not a directory'

        setters = [
            PropertySetter('image', required=True, on_error=throw_property_error),
            PropertySetter('library', required=False, validate=validate_file_library, on_error=throw_property_error),
            PropertySetter('custom_commands', required=False, validate=custom_command_path_validator,
                           on_error=throw_property_error)
        ]

        data.set_properties(setters, self)

        dockerfile_data = data.get_property('dockerfile')

        if dockerfile_data is None:
            raise BuildConfigurationError(f'dockerfile is a required property')

        self.dockerfile.initialise(dockerfile_data)

        self._convert_custom_commands()

        files_data = BuildFileData({
            'files': data.get_property('files')
        })
        steps_data = BuildFileData({
            'steps': data.get_property('steps')
        })
        post_steps_data = BuildFileData({
            'post': data.get_property('post')
        })

        self.files = Files().initialise(files_data).files
        self.steps = BuildSteps().initialise(steps_data).steps

        if post_steps_data.get_property('post') is not None:
            self.post_steps = BuildSteps(post_build=True).initialise(post_steps_data).steps
