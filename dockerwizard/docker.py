"""
A module to encapsulate Docker behaviour
"""
from .process import Execution


class DockerClient:
    """
    A client for interacting with Docker. The methods are simply wrappers around setting up the Execution required for
    the given docker command and returning the result
    """
    @staticmethod
    def build_docker_image(tag: str, workdir: str = '.'):
        """
        Build the docker image using the provided tag and workdir for the docker build context
        """
        args = ['docker', 'build', '--tag', tag, workdir]

        return Execution(args).execute()

    @staticmethod
    def create_docker_container(tag: str, name: str, extra_args: list):
        """
        Create the docker container using docker run. All containers are run in detached mode (-d)
        """
        args = ['docker', 'run', '-d', '--name', name]

        for value in extra_args:
            args.append(value)

        args.append(tag)

        return Execution(args).execute()
