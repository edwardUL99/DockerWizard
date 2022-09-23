"""
Utilities for the integration package
"""
import sys


def print_formatted_command_output(msg: str, tag: str, success: bool):
    """
    Prints formatted command output
    :param msg: the message to print
    :param tag: the tag of the command
    :param success: true if succeeded, false if not
    """
    equals_output_pattern = ''.join(["="] * (len(msg) + 4))
    status = 'SUCCESS' if success else 'FAILURE'
    status_output = f'\n{tag}\n{equals_output_pattern}\n| {msg} |\n{equals_output_pattern}\n\n{status}'

    print(status_output, file=sys.stderr if not success else None)
