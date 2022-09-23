"""
Allows generation of a base integration test directory
"""
import argparse
import os
import sys
import shutil

from utils import print_formatted_command_output
from interfaces import IntegrationProgram


class IntegrationGenerationProgram(IntegrationProgram):
    """
    A program to generate integration tests
    """

    def __init__(self, subparsers):
        super().__init__('create', 'Allows the generation of an integration test directory '
                                   'populating it with defaults', subparsers)

    def initialise_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('directory', help='The directory to create and populate with integration test files')

    @staticmethod
    def _populate_files(directory: str):
        os.makedirs(directory)
        build_file = os.path.join(directory, 'build.yaml')
        spec_file = os.path.join(directory, 'spec.yaml')
        it_file = os.path.join(directory, 'it.py')
        post_file = os.path.join(directory, 'post.py')

        shutil.copy(os.path.join('resources', '_build.yaml'), build_file)
        shutil.copy(os.path.join('resources', '_spec.yaml'), spec_file)
        shutil.copy(os.path.join('resources', '_it_library.py'), it_file)
        shutil.copy(os.path.join('resources', '_post_sample.py'), post_file)

    def run(self, args: argparse.Namespace):
        directory = args.directory

        if directory.endswith('/'):
            directory = directory[:-1]

        directory = directory if os.path.isabs(directory) else os.path.join(os.getcwd(), directory)
        name = os.path.basename(directory)

        if os.path.isdir(directory):
            print(f'Directory {directory} already exists', file=sys.stderr)
            print_formatted_command_output(name, 'Integration Test Generation', False)
            sys.exit(1)

        os.chdir(os.path.dirname(__file__))

        IntegrationGenerationProgram._populate_files(directory)

        print(f'An integration test directory has been generated in {directory}.\n'
              'Edit the build.yaml and spec.yaml files for this integration test\n'
              'Use mockproggen.py to generate mock programs\n'
              'Edit the generated post.py file to write post build log verification tests')

        print_formatted_command_output(name, 'Integration Test Generation', True)
