"""
Constants for the project
"""
import os

# the version of the tool
VERSION = '1.0.0a13 (alpha)'

# name of environment variable for docker wizard home
DOCKER_WIZARD_HOME_VAR = 'DOCKER_WIZARD_HOME'

# the home path of the project
DOCKER_WIZARD_HOME = os.environ.get(DOCKER_WIZARD_HOME_VAR)

# name of environment variable for docker wizard command name
DOCKER_WIZARD_CMD_NAME_VAR = 'DOCKER_WIZARD_CMD_NAME'

# the name of the command to run the tool
DOCKER_WIZARD_CMD_NAME = os.environ.get(DOCKER_WIZARD_CMD_NAME_VAR, 'docker-wizard')

# On windows, a path to a bash emulator can be setup, e.g. git bash, if WSL bash isn't available
DOCKER_WIZARD_BASH_PATH = os.environ.get('DOCKER_WIZARD_BASH_PATH')

# the default name for the custom commands file
CUSTOM_COMMANDS = 'custom-commands.yaml'

# name of environment variable flag to identify if testing is in progress
DOCKER_WIZARD_TESTING_NAME = 'DOCKER_WIZARD_TESTING'

