"""
A module that holds classes that can parse a build file
"""
from abc import ABC, abstractmethod

import yaml

from .models import DockerBuild, throw_property_error, BuildFileData
from .cli import info


__all__ = ['BuildParser', 'get_build_parser']


class BuildParser(ABC):
    """
    A class that can parse a build file to a DockerBuild
    """
    @abstractmethod
    def parse(self, file: str) -> DockerBuild:
        pass


def convert_dict_to_build_data(data: dict) -> BuildFileData:
    """
    Converts a dictionary to build file data
    :param data: the data to convert
    :return: the converted data
    """
    converted = {}

    for key, value in data.items():
        if isinstance(value, dict):
            converted[key] = convert_dict_to_build_data(value)
        elif isinstance(value, list):
            converted[key] = [convert_dict_to_build_data(v) if isinstance(v, dict) else v for v in value]
        else:
            converted[key] = value

    return BuildFileData(converted)


class YamlBuildParser(BuildParser):
    """
    Allows parsing of a build from a YAML file
    """
    def parse(self, file: str) -> DockerBuild:
        info(f'Parsing build file {file}')
        try:
            with open(file, 'r') as stream:
                data = yaml.safe_load(stream)

            if 'build' not in data:
                throw_property_error(f'{file} is an invalid build configuration file as it does not contain a build tag')

            config_data = convert_dict_to_build_data(data['build'])

            return DockerBuild().initialise(config_data)
        except FileNotFoundError:
            throw_property_error(f'Build Configuration File {file} does not exist')


def get_build_parser() -> BuildParser:
    """
    Get the implementation of the build parser
    :return: current implementation of the build parser
    """
    return YamlBuildParser()
