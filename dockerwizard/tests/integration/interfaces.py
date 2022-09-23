"""
Provides interfaces for integration module
"""
import argparse
from abc import ABC, abstractmethod


class IntegrationProgram(ABC):
    """
    A base class that defines a program for the itutils utility
    """
    def __init__(self, name: str, description: str, subparsers):
        """
        Initialise the program. The children should have the signature __init__(subparsers) but call super with the
        name and description
        :param name: the name of the program
        :param description: the program description
        :param subparsers: passed in by itutils
        """
        self.name = name
        parser = subparsers.add_parser(name, help=description)
        self.initialise_arguments(parser)

    @abstractmethod
    def initialise_arguments(self, parser: argparse.ArgumentParser):
        """
        Add all the required arguments to the provided parser
        """
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace):
        """
        Run the program with the provided arguments
        :param args: the parsed arguments
        """
        pass


def construct_program(subparsers, program: type) -> IntegrationProgram:
    """
    A factory to construct a subclass of integration program identified by program
    :param subparsers: the subparsers to pass to init
    :param program: the program to create
    """
    if not issubclass(program, IntegrationProgram):
        raise ValueError(f'{program} is not a subclass of IntegrationProgram')
    else:
        return program(subparsers)
