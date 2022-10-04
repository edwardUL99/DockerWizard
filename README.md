docker-wizard: A tool to run build steps before Docker image build
===
This project allows you to define a build file using a YAML specification which outlines a series of steps
that should be executed before the subsequent Docker build of the image. These steps can be viewed as pre-processing 
steps that need to be performed before you build the Docker image. Take the following use case:
- You have a Python program that reads a file and outputs the file. This file contains a message the Python program
reads back
- To build this image, you need to:
  - Create the message file with the message to be printed set as an environment variable
  - Copy the message file over to the Docker image
  - Copy the Python script over to the Docker image
- To do those steps, you need to have the Dockerfile, message file and Python script in some working directory, which is
known as the **build directory** in this project.
- With the project, you can define the files required which will be copied over to the build directory and also the
steps required to prepare the build directory for the Docker build command

While this use case is quite trivial, it can be extended to cases for example, where you are deploying a Java Spring
Boot application to a Docker container. These applications generally has properties contained within *application.properties*
files. You could store a centrally located properties file for the environment that you may not want to commit to the
application repository. Then, you can create a build file that clones the app's Git repository, copies the properties
into the cloned version, run a Maven build, copy over the build JAR file to the build directory and subsequently build
the image.

The builds are entirely configurable using built-in commands for the build steps as well as the possibility of defining
custom commands.

## Requirements
- python 3.8 minimum installed with the command `python` for that version available on the PATH
- pip for the python version installed
- docker installed
- If you are running the tool on Windows and wish to specify bash commands in the `execute-shell` command, you need a Bash emulator installed. If you have
Windows Subsystem for Linux (WSL) setup, you don't need to do anything since the `bash` command is available as part of
WSL. Otherwise, you need to set an environment variable called `DOCKER_WIZARD_BASH_PATH` which contains the path to your
Bash emulator executable, for example, if you have `Git Bash` installed, you can run:
```
set DOCKER_WIZARD_BASH_PATH='"C:\Program Files\Git\bin\bash.exe"'
```
**Note:** It is recommended to create separate build files for Unix environments and Windows environments for best
compatibility as the stability of the build cannot be guaranteed

## Installation
To install the project, perform the following steps:
- Set an environment variable `DOCKER_WIZARD_HOME` as an absolute path to the root of the project, i.e. where this
README is located, e.g. `/home/jdoe/DockerWizard` assuming you cloned the repository into DockerWizard
- Add `DOCKER_WIZARD_HOME/bin` to your system path
- In a terminal, change directory to `DOCKER_WIZARD_HOME` and run:
```bash
pip install -r requirements.txt
```
- **Optional but recommended** In a terminal, change directory to `DOCKER_WIZARD_HOME` and run:
```bash
python setup.py install
```
This step enables you to import the `dockerwizard` framework package (which contains modules for the project) without
adding `DOCKER_WIZARD_HOME` to the system path when defining commands

A useful sanity check to ensure that the system will work from an installation point of view is to run the following
(replace `<DOCKER_WIZARD_HOME>` with `$DOCKER_WIZARD_HOME` on bash or `%DOCKER_WIZARD_HOME%` on Windows:
```bash
<DOCKER_WIZARD_HOME>/bin/docker-wizard -v
```
And verify that the output has no error messages (for example, there may be a Docker version error if Docker is
not installed)

## Run
To run the tool, you have the following usage:

`docker-wizard [-h] [-w  WORKDIR] [-c CUSTOM] [-v] [-b] file`

The arguments are as follows:
- **-h**: Prints usage help information
- **-w**: Specify the working directory (not build directory) to retrieve `file` from
- **-c**: Custom path to custom commands specification file, otherwise `custom-commands.yaml` is attempted to be
retrieved from project directory or `DOCKER_WIZARD_HOME`
- **-v**: Print the version and system information for the tool and immediately exit
- **-b**: Print help information for all the builtin commands in the tool (similar to the builtin commands descriptions
below) and immediately exit
- **file**: The path relative to the working directory either from where the command is run or specified by `-w` to the
build specification file

## Tests
The project has a set of automated unit tests which can be run using the following command (on Windows use the cmd file)
from the root of the project:
```bash
dockerwizard/tests/test
```
If you see output like:
```bash
...............................
.........................
Ran X tests in x.xxxs

OK
```
it means that the tests have passed successfully with no errors. If there are any failures, it indicates that there may
be a bug (due to coding error, python/library version inconsistencies or a breaking change)

## Build Specification
A build is specified in a build file using YAML. The following file is a sample build file in the
`example/` directory:

[build.yaml](example/build.yaml)
```yaml
# A build object is identified by the build tag
build:
  # image represents the tag name of the resulting Docker image
  image: 'hello-world-docker-build'
  # file object representing dockerfile
  dockerfile:
    path: 'Dockerfile'
  # specifies a path to where files should be retrieved from when relative to file library
  library: 'files'
  custom_commands: 'custom-commands.yaml'
  # list of file objects to copy to build directory
  files:
    - path: 'hello-world.py'
    # can also define absolute path (same with dockerfile)
    # - path: '/absolute/path/to/file'
    #   relative_to_library: false
    - path: 'set-message.sh'
  # steps to execute before building the docker image
  steps:
    # steps are executed with build directory as the working directory
    # after each step executes, the working directory is reset to the build directory
    - name: 'Set message environment variable'
      command: 'set-variable'
      arguments:
        - 'MESSAGE'
        - 'Hello World from the sample DockerBuild build file'
    - name: 'Set multiple variables to demonstrate set-variables command'
      command: 'set-variables'
      arguments:
        - 'key1=this is a value'
        - 'key2=this is another value'
    - name: 'Print variables to verify variables are set'
      command: 'execute-shell'
      arguments:
        - 'echo'
        - '"Value of key1 is: $key1"'
        - '&&'
        - 'echo'
        - '"Value of key2 is: $key2"'
    - name: 'Generate message.txt using set-message.sh'
      command: 'execute-shell'
      named:
        key: 'value'
      arguments:
        - 'bash' # if Windows, the framework will try to resolve bash to a bash emulator either through WSL or set with DOCKER_WIZARD_BASH_PATH env variable
        - 'set-message.sh'
    - name: 'View contents of build directory after build'
      command: 'execute-shell'
      # execute-shell does not use named arguments but is a demonstration of how to use them. Any validation is to be
      # done by the implementing command as only positional arguments can be validated for number of arguments required
      # etc. Currently implemented should a custom command needs the concept of key-value arguments. The step object
      # can be accessed through self.build_context.current_step in the command execute method
      named:
        key: 'value'
        purpose: 'Allows named arguments'
      arguments:
        - 'ls'
        - '-al'
    # after steps complete, the framework will run docker build
  post:
    # optional steps to run after successful docker build
    - name: 'Create a container from the built image'
      command: 'create-container'
      arguments:
        - 'hello-world'
        - 'hello-world-docker-build'
```
This example is designed to run on Unix machines. To run it, run the following command from root of project:

`docker-wizard -w example build.yaml`

## Commands
Build steps are executed by specifying an optional name to display on the build output, a command to run the step and a
list of arguments to the command. The list of built-in commands are as follows:

### Built-in Commands
- **copy**: Copies a source file to a destination relative to build directory
  - *Arguments*: 2 arguments
    - 1: Source file
    - 2: Destination
- **execute-shell**: Executes a system command using the system shell (bash or cmd, e.g.)
  - *Arguments*: 1 or more arguments which are joined together and passed to the shell
  - If the first argument is `bash` and the OS is windows, it will be resolved to a Bash emulator, see requirements.
- **set-variable**: Sets an environment variable with provided value, logging it to the console
  - *Arguments*: 2 arguments
    - 1: Name of the variable
    - 2: Value
- **set-secret**: Sets an environment variable with provided value, however does not log the value to console since the
value is treated as a secret
  - *Arguments*: 2 arguments
    - 1: Name of the variable
    - 2: Value
- **set-variables**: Provides the ability to set multiple environment variables by supplying key=value pairs
  - *Arguments*: 1 or more arguments
- **git-clone**: Clones a git repository into the build directory
  - *Arguments*: At least 1 argument, with optional 2nd argument
    - 1: URL of git repository
    - 2: Optional name of target directory to clone into
- **execute-groovy**: Executes a groovy script
  - *Arguments*: 1 or more arguments where one of the arguments must be a groovy script file ending in .groovy. The rest
  of the arguments can be flags passed to the groovy interpreter
- **execute-python**: Executes a python script
  - *Arguments*: 1 or more arguments where one of the arguments must be a python script file ending in .py. The rest of
  the arguments can be flags passed to the python interpreter
- **create-container**: Create a Docker container. Always creates containers in detached mode (-d)
  - *Arguments*: 2 or more arguments can be provided but the order must match the following
    - 1: The name of the container to create
    - 2: The tag/image of the container to run. Any command to execute in the created container can be passed into this
    string also, separated by spaces
    - *optional extra arguments like -p, --network etc. to pass to the docker run command*

### Custom Commands
You can define your own custom commands to perform your use-case specific tasks. The general process for defining a
custom command is as follows:
- Create a python file to contain the command (or multiple custom commands)
- Add the `DOCKER_WIZARD_HOME` env variable value to the `sys.path` object if `setup.py` has not been run
- Import the `AbstractCommand` class from the `dockerwizard.commands` module
- If the command wants to throw errors, import `CommandError` from the `dockerwizard.errors` module
- If the command wants to output to the console, it can do so with the `dockerwizard.cli` module
- Create a class that extends `AbstractCommand` and in the `__init__` method, call `super().__init__()` with the name
of the command (name is what is referred to in the build file) and arguments required
- In the created class, override the `_execute` method which is a hook called by `AbstractCommand` after validating
arguments
- If the command needs to throw an error, raise an instance of `CommandError`
- Then, define a custom-commands.yaml file in the project working directory or a
`DOCKER_WIZARD_HOME/custom-commands.yaml` file with the following structure:
```yaml
# If the file path is relative, it is read relative to the directory the custom-commands.yaml file is in
commands:
  - file: 'path/to/file.py'
    class: 'SampleCustomCommand'
```
You can also define the file somewhere else and pass the path in with the **-c** flag. The search order is as follows:
1. Path passed in with the **-c** flag. If it is relative, it is resolved relative to build working directory
2. `custom-commands.yaml` file found in project working directory
3. `custom-commands.yaml` file found in the `DOCKER_WIZARD_HOME` directory

The following is a sample custom-commands.yaml file and a sample python file (both contained in `example`)
containing the definitions of a sample command:

[custom-commands.yaml](example/custom-commands.yaml)
```yaml
# If the file path is relative, it is read relative to the directory the custom-commands.yaml file is in
commands:
  - file: 'custom.py'
    class: 'SampleCustomCommand'
```

[custom.py](example/custom.py)

```python
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

    cli.info('Named arguments in the context\'s current build step are '
             f'{self.build_context.current_step.named})')

  def default_name(self):
    # allows a default name to be assigned when the name tag is not provided in the build step
    return 'Sample Custom Command'
```
This command simply prints out the arguments passed in and for demonstration purposes if the argument contains
'throw-error' and error will be thrown.

#### Build Context
In the custom command implementing AbstractCommand, you can access the build context using `self.build_context()`. 
The context instance holds properties like the current build step
and the build config. The framework initialises the context object before the build starts