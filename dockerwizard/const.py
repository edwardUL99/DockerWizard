"""
Constants for the project
"""
import os

# the version of the tool
VERSION = '1.0.0a4 (alpha)'

# name of environment variable for docker wizard home
DOCKER_WIZARD_HOME_VAR = 'DOCKER_WIZARD_HOME'

# the home path of the project
DOCKER_WIZARD_HOME = os.environ.get(DOCKER_WIZARD_HOME_VAR)

# name of environment variable for docker wizard command name
DOCKER_WIZARD_CMD_NAME_VAR = 'DOCKER_WIZARD_CMD_NAME'

# the name of the command to run the tool
DOCKER_WIZARD_CMD_NAME = os.environ.get(DOCKER_WIZARD_CMD_NAME_VAR)
DOCKER_WIZARD_CMD_NAME = DOCKER_WIZARD_CMD_NAME if DOCKER_WIZARD_CMD_NAME else 'DockerWizard'

# the default name for the custom commands file
CUSTOM_COMMANDS = 'custom-commands.yaml'

