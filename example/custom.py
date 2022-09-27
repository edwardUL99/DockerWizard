from sys import path
from os import environ

# add the project home to build so imports will work
project_home = environ.get('DOCKER_WIZARD_HOME')

if project_home not in path:
    path.append(project_home)

# custom commands should extend this abstract command
from dockerwizard import AbstractCommand
# any command errors should be raised as an instance of CommandError
from dockerwizard import CommandError
from dockerwizard import cli


class SampleCustomCommand(AbstractCommand):
    """
    This sample custom command simply just prints the arguments provided to it
    """
    def __init__(self):
        # init the command with sample-custom-command which can be referenced from build files
        # The command requires at least (at_least=True) 1 (num_args_required) arguments
        super().__init__(name='sample-custom-command', num_args_required=1, at_least=True)

    def _execute(self, args: list):
        # this is the 'hook' that you extend for the command. AbstractCommand.execute validates the number of args and
        # on successful validation, calls this
        cli.info(f'The arguments passed to {self.default_name()} are:')

        for arg in args:
            cli.info(f'\t{arg}')

        try:
            if args.index("throw-error"):
                # demo purposes if args contain throw-error, raise a CommandError
                raise CommandError('This is how you raise an error condition from the command')
        except ValueError:
            pass  # not in the list so ignore

    def default_name(self):
        # allows a default name to be assigned when the name tag is not provided in the build step
        return 'Sample Custom Command'
