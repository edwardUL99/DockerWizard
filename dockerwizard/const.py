"""
Constants for the project
"""
import os

# name of environment variable for docker wizard home
DOCKER_WIZARD_HOME_VAR = 'DOCKER_WIZARD_HOME'

# the home path of the project
DOCKER_WIZARD_HOME = os.environ.get(DOCKER_WIZARD_HOME_VAR)

# the default name for the custom commands file
CUSTOM_COMMANDS = 'custom-commands.yaml'

# name of command to display in help for argparser
COMMAND_NAME = 'DOCKER_WIZARD_CMD_NAME'

