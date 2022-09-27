"""
An integration test runner by running dockerwizard from a specification file
"""
import argparse
import platform
import subprocess
import sys
from typing import List
import glob
import yaml
import os

from utils import print_formatted_command_output
from interfaces import IntegrationProgram

TEST_RETURN_CODE = 'DOCKER_BUILD_TEST_CODE'

ARGUMENTS_BASE = 'MOCK_PROGRAM_ARGS_'
OUTPUT_BASE = 'MOCK_PROGRAM_OUTPUT_'
TEST_BUILD_FILE = 'build_test.yaml'

DOCKER_WIZARD_HOME = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir,
                                                  os.path.pardir))
os.environ['DOCKER_WIZARD_HOME'] = DOCKER_WIZARD_HOME


class _SkipTest(RuntimeError):
    pass


class IntegrationRunnerProgram(IntegrationProgram):
    """
    A program that can run an integration test
    """

    def __init__(self, subparsers):
        super().__init__('run', 'Allows the running of an integration test', subparsers)

    def initialise_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('-g', '--glob', action='store_true', help='If specified, the directory argument'
                                                                      ' is treated as a glob to execute multiple'
                                                                      ' integration tests')
        parser.add_argument('directory', help='The directory of the integration test')

    @staticmethod
    def _print_failed(directory: str):
        print_formatted_command_output(os.path.basename(directory), 'Integration Test', False)

    @staticmethod
    def _validate_directory(directory, skip: bool = False):
        if not os.path.isabs(directory):
            directory = os.path.join(os.getcwd(), directory)

        if os.path.isdir(directory):
            spec = os.path.join(directory, 'spec.yaml')

            if not os.path.isfile(spec):
                if not skip:
                    print(f'Spec file {spec} is not a file', file=sys.stderr)
                    IntegrationRunnerProgram._print_failed(directory)
                    sys.exit(2)
                else:
                    raise _SkipTest

            return directory
        else:
            if not skip:
                print(f'{directory} is not a directory', file=sys.stderr)
                IntegrationRunnerProgram._print_failed(directory)
                sys.exit(1)
            else:
                raise _SkipTest

    @staticmethod
    def _validate_spec(spec, directory):
        programs = spec.get('mock_programs')

        if programs:
            for program in programs:
                file = program.get('file')
                if not os.path.isfile(file):
                    print(f'Mock program {file} does not exist', file=sys.stderr)
                    IntegrationRunnerProgram._print_failed(directory)
                    sys.exit(3)

        args = spec.get('args')

        if not args:
            print(f'Args to pass to dockerwizard must be specified')

    @staticmethod
    def _set_program_variables(base: str, variables: dict):
        for key, value in variables.items():
            os.environ[f'{base}{key}'] = value

    @staticmethod
    def _write(file: str, output: str):
        with open(file, 'w') as f:
            f.write(output)

    @staticmethod
    def _prepare_build_file(directory: str, mock_programs: List):
        def _create_file(mock: dict):
            file = mock.get('file')
            file = file if os.path.isabs(file) else os.path.join(directory, file)

            return {'path': file, 'relative_to_library': False}

        build_file = os.path.join(directory, 'build.yaml')

        with open(build_file, 'r') as stream:
            build = yaml.safe_load(stream)

        files = build.get('files', [])

        if mock_programs:
            files.extend([_create_file(mock) for mock in mock_programs])

        build['files'] = files
        test_build = os.path.join(directory, TEST_BUILD_FILE)

        with open(test_build, 'w') as stream:
            yaml.safe_dump(build, stream)
            stream.flush()

        return test_build

    @staticmethod
    def _find_and_create_build_file(directory: str, args: List[str], mock_programs: List):
        workdir = directory

        for i, val in enumerate(args):
            if val == '-w' or val == '--workdir':
                if i + 1 < len(args):
                    workdir = args[i + 1]
                    break
                else:
                    raise ValueError('-w/--workdir in args specified incorrectly')
            elif val == 'build.yaml':
                args[i] = TEST_BUILD_FILE  # interpolate test build

        if not os.path.abspath(workdir):
            workdir = os.path.join(directory, workdir)

        return IntegrationRunnerProgram._prepare_build_file(workdir, mock_programs)

    @staticmethod
    def _clean_envs_files(directory: str):
        files = glob.glob(os.path.join(directory, '*_envs.yaml'))

        for file in files:
            os.remove(file)

    @staticmethod
    def _execute_post(process, post, directory, directory_name):
        os.environ[TEST_RETURN_CODE] = f'{process.returncode}'
        clean_files = process.returncode == 0
        process = subprocess.Popen(['python', post], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            print(f'{post} failed with stdout: {stdout}, stderr: {stderr} and return code {process.returncode}',
                  file=sys.stderr)
            print_formatted_command_output(directory_name, 'Integration Test', False)
            sys.exit(4)
        else:
            print(f'Post execution verification file {post} executed successfully')

        if clean_files:
            os.remove('stdout.txt')
            os.remove('stderr.txt')
            IntegrationRunnerProgram._clean_envs_files(directory)

    @staticmethod
    def _check_build(process, stdout, stderr, directory_name):
        if process.returncode != 0:
            print(f'Build failed with stdout: {stdout}, stderr: {stderr} and return code {process.returncode}',
                  file=sys.stderr)
            print_formatted_command_output(directory_name, 'Integration Test', False)
            sys.exit(5)

    @staticmethod
    def _execute_build_and_post(args: List[str], old_path: str, directory: str, build_file: str):
        directory_name = os.path.basename(directory)
        print(f'Executing integration test {directory_name}')
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        os.environ['PATH'] = old_path
        os.remove(build_file)
        post = os.path.join(directory, 'post.py')

        IntegrationRunnerProgram._write('stdout.txt', stdout)
        IntegrationRunnerProgram._write('stderr.txt', stderr)

        IntegrationRunnerProgram._check_build(process, stdout, stderr, directory_name)

        if os.path.isfile(post):
            IntegrationRunnerProgram._execute_post(process, post, directory, directory_name)

            print_formatted_command_output(directory_name, 'Integration Test', True)

    @staticmethod
    def _prepare_build(path: str, directory: str, mock_programs: list, spec_args: str):
        program_args = {}
        program_output = {}

        if mock_programs:
            for program in mock_programs:
                file = os.path.join(directory, program.get('file'))
                filename = os.path.basename(file).upper()
                file_dir = os.path.dirname(file)

                if file_dir not in path:
                    path = f'{file_dir}{os.pathsep}{path}'

                file_args = program.get('args')
                file_output = program.get('output')
                program_args[filename] = file_args if file_args else None
                program_output[filename] = file_output if file_output else None

            os.environ['PATH'] = path

        wizard_script = 'docker-wizard.cmd' if platform.system().lower() == 'windows' else 'docker-wizard'
        args: List[str] = [os.path.join(DOCKER_WIZARD_HOME, 'bin', wizard_script)]
        args.extend([arg for arg in spec_args.split(' ')])

        IntegrationRunnerProgram._set_program_variables(ARGUMENTS_BASE, program_args)
        IntegrationRunnerProgram._set_program_variables(OUTPUT_BASE, program_output)

        build_file = IntegrationRunnerProgram._find_and_create_build_file(directory, args, mock_programs)

        return args, build_file

    @staticmethod
    def _execute_spec(spec):
        directory = os.getcwd()
        old_path = os.environ['PATH']
        new_path = old_path

        mock_programs = spec.get('mock_programs')

        args, build_file = IntegrationRunnerProgram._prepare_build(new_path, directory, mock_programs, spec.get('args'))

        IntegrationRunnerProgram._execute_build_and_post(args, old_path, directory, build_file)

    @staticmethod
    def _parse_spec(spec_file: str):
        with open(spec_file, 'r') as stream:
            return yaml.safe_load(stream)

    @staticmethod
    def _execute(directory: str, glob_part: bool):
        if directory.endswith('/'):
            directory = directory[:-1]

        directory = IntegrationRunnerProgram._validate_directory(directory, skip=glob_part)
        spec = IntegrationRunnerProgram._parse_spec(os.path.join(directory, 'spec.yaml'))
        previous_dir = os.getcwd()
        os.chdir(directory)
        IntegrationRunnerProgram._validate_spec(spec, directory)
        IntegrationRunnerProgram._execute_spec(spec)
        os.chdir(previous_dir)

    def run(self, args: argparse.Namespace):
        do_glob = args.glob
        directory = args.directory
        tests = [directory] if not do_glob else glob.glob(directory)

        if len(tests) == 0:
            print('No tests found, exiting...')
        else:
            for test in tests:
                try:
                    IntegrationRunnerProgram._execute(test, glob_part=do_glob)
                except _SkipTest:
                    print(f'Warning: {test} does not contain a spec.yaml file, skipping...')
