"""
Generates a mockprogram file
"""
import argparse
import string
import os
import stat
import sys

from utils import print_formatted_command_output
from interfaces import IntegrationProgram


class MockProgramGenerationProgram(IntegrationProgram):
    """
    A program to generate mock programs
    """
    def __init__(self, subparsers):
        super().__init__('program', 'Allows the generation of mock programs which can mock real programs'
                                    ' in a build file', subparsers)

    def initialise_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('-d', '--directory', required=False, default=os.getcwd(), help='The output directory')
        parser.add_argument('-a', '--arguments', required=False, default=None,
                            help='Specify hard coded defaults if environment variable for arguments are not set which '
                                 'are hard coded into the generated file. The format should match that in a spec file')
        parser.add_argument('-o', '--outputs', required=False, default=None,
                            help='Specify hard coded defaults if environment variable for outputs are not set which are'
                                 ' hard coded into the generated file. The format should match that in a spec file')
        parser.add_argument('-t', '--test', help='The name of the integration test (integration tests are stored under '
                                                 'docker_wizard_home/dockerwizard/tests with names in the format '
                                                 '<name>_integration')
        parser.add_argument('name', help='The name of the output file')

    @staticmethod
    def _write_windows_script(output: str):
        # a windows script is output to allow execution on windows
        name = os.path.basename(output)
        path = os.path.join(os.path.dirname(output), f'{name}.cmd')
        with open(path, 'w') as f:
            f.write(f'@echo off\n\ncall python %~dp0\\{name} %*\n\nexit /b %ERRORLEVEL%\n')

    @staticmethod
    def _create_file(source: str, output: str, test: str, args: str, parsed_output: str):
        with open(source, 'r') as template, open(output, 'w') as output_file:
            src = string.Template(template.read())
            sub = {
                'ARGS': '$ARGS' if args is None else args,
                'OUTPUT': '$OUTPUT' if parsed_output is None else parsed_output,
                'TEST': test
            }
            result = src.substitute(sub)

            output_file.write(result)

            MockProgramGenerationProgram._write_windows_script(output)

    def run(self, args):
        output_dir = args.directory

        if not os.path.isdir(output_dir):
            print(f'{output_dir} is not a directory', file=sys.stderr)
            print_formatted_command_output(args.name, 'Mock Program Generation', False)
            sys.exit(1)
        else:
            output_dir = os.path.abspath(output_dir)
            file = os.path.join(os.path.dirname(__file__), 'mockprogram.py')
            output = os.path.join(output_dir, args.name)
            MockProgramGenerationProgram._create_file(file, output,
                                                      args.test,
                                                      args.arguments, args.outputs)
            st = os.stat(output)
            os.chmod(output, st.st_mode | stat.S_IEXEC)
            print(f'Mock program executable with name {args.name} generated successfully into {output}')
            print_formatted_command_output(args.name, 'Mock Program Generation', True)
