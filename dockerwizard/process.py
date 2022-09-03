"""
An abstraction to allow execution of an external process
"""
from subprocess import Popen, PIPE
from typing import Union, List


class ExecutionResult:
    """
    The result of a process execution
    """
    def __init__(self, exit_code: int, stdout: str, stderr: str):
        """
        Initialise the execution result with the given parameters
        :param exit_code: the exist code of the process
        :param stdout: the standard output of the process
        :param stderr: the standard error of the process
        """
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def is_healthy(self):
        """
        Returns true if process executed normally (exit code 0) or false if non-zero
        :return: true if exit code is 0
        """
        return self.exit_code == 0


class Execution:
    """
    Encapsulates the execution of a command
    """
    def __init__(self, command: Union[str, List[str]]):
        """
        Creates an execution object with the command to execute
        :param command: a command as a string or list of arguments
        """
        if isinstance(command, list):
            command = ' '.join(command)
        self._process = Popen(command, stdout=PIPE, stderr=PIPE, text=True, shell=True)

    def execute(self) -> ExecutionResult:
        """
        Begins the execution and waits for it to complete, returning the result
        :return: the result
        """
        stdout, stderr = self._process.communicate()

        return ExecutionResult(self._process.returncode, stdout, stderr)
