"""
This provides the main script for the tool which uses the dockerwizard library entrypoint module to start the system.
Other way of executing is running python -m dockerwizard
"""

from dockerwizard import entrypoint


if __name__ == '__main__':
    entrypoint.main()
