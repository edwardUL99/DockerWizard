from dockerwizard import AbstractCommand, cli


class TestCustomCommand(AbstractCommand):
    def __init__(self):
        super().__init__('test-command', 0)

    def _execute(self, args: list):
        context = self.build_context

        cli.info(f'Current Step name is {context.current_step.name}')
        cli.info(f'Current Step named arguments are {context.current_step.named}')
