"""
This module holds the classes required for building the docker images
"""
import shutil
import os

from .models import DockerBuild, File, BuildStep
from .workdir import create_temp_directory, change_directory, change_back
from .cli import info, error
from .commands import registry
from .builtincommands import register_builtins
from .errors import CommandError, BuildFailedError, BuildConfigurationError
from .process import Execution

register_builtins()


class Builder:
    """
    The class that holds the responsibility of building the docker images
    """
    def __init__(self, config: DockerBuild):
        """
        Initialise the builder with the configuration it is intended to build
        :param config: the config this builder is going to build
        """
        self.config = config
        self._working_directory = create_temp_directory()

    def _copy_file(self, file: File, dockerfile: bool = False):
        """
        Copies the file to the working directory
        :param file: the file to copy
        :return: None
        """
        file_type = 'Dockerfile' if dockerfile else 'file'

        if file.relative_to_library:
            info(f'Copying {file_type} {file.path} from library to build directory')
            full_path = os.path.join(self.config.library, file.path)
        else:
            info(f'Copying {file_type} {file.path} to build directory')
            full_path = file.path

        shutil.copy(full_path, self._working_directory.name)

    def _copy_files(self):
        """
        Copies files required by the build to the build directory
        :return: None
        """
        info('Copying Dockerfile and required files to build directory')

        # copy the Dockerfile
        self._copy_file(self.config.dockerfile, True)

        # copy all required files
        for file in self.config.files:
            self._copy_file(file)

        info('Dockerfile and required files successfully copied to build directory')

    @staticmethod
    def _execute_step(index: int, step: BuildStep):
        """
        Execute the build step
        :param index: the index of this step
        :param step: the step to execute
        :return: None
        """
        try:
            name = step.name
            command = step.command
            args = step.arguments

            try:
                command_implementation = registry.get_command(command)
                name = name if name else command_implementation.default_name()
                info(f'Executing build step {index} - {name}')

                command_implementation.execute(args)
            except ValueError:
                raise BuildConfigurationError(f'Unknown command {command} in configuration build step'
                                              f' {index}')
        except CommandError as e:
            error(f'Failed to execute build step {index} - {step.name} with error {e.message}')
            raise BuildFailedError()

    def _execute_steps(self):
        """
        Execute the build steps
        :return: None
        """
        info('Executing build steps')

        for i, val in enumerate(self.config.steps):
            self._execute_step(i + 1, val)
            change_directory(self._working_directory.name, not_store=True)

    def _build_docker_image(self):
        """
        Builds the docker image after successful completion of steps
        :return: None
        """
        info(f'Building Docker image with tag {self.config.image}')
        args = ['docker', 'build', '--tag', self.config.image, '.']
        execution = Execution(args).execute()

        if not execution.is_healthy():
            error(f'Failed to build Docker image with error {execution.stderr} and exit code {execution.exit_code}')
            raise BuildFailedError()
        else:
            info(f'Docker image with tag {self.config.image} built successfully with the following output:')
            split = execution.stdout.splitlines()

            for line in split:
                info(f'\t{line}')

    def _clean_build_directory(self):
        """
        Attempts to clean up the build directory, silently ignoring errors. Other errors are thrown
        """
        try:
            self._working_directory.cleanup()
        except OSError:
            pass

    def build(self):
        """
        Builds the docker image identified by the provided config
        :return: True if build succeeded, false if not
        """
        failed = False

        try:
            self._copy_files()

            info('Changing working directory to build directory')
            change_directory(self._working_directory.name)

            self._execute_steps()
            self._build_docker_image()

            info('Build finished, changing back to working directory')
            info('BUILD SUCCEEDED')
        except BuildFailedError:
            error('See logs to see why the build failed')
            error('BUILD FAILED')
            failed = True

        change_back()
        self._clean_build_directory()

        return not failed
