"""
Tests the context module
"""
import contextlib
import unittest

from dockerwizard.errors import BuildContextError
from .testing import main
from dockerwizard.context import BuildContext, initialise, teardown
from dockerwizard.models import DockerBuild, BuildStep


class BuildContextTest(unittest.TestCase):
    def setUp(self) -> None:
        BuildContext._INSTANCE = None

    def test_properties(self):
        context = BuildContext()
        self.assertIsNone(context.config)
        self.assertIsNone(context.current_step)

        config = DockerBuild()
        step = BuildStep()

        context.config = config
        context.current_step = step

        self.assertEqual(config, context.config)
        self.assertEqual(step, context.current_step)

    def test_initialise(self):
        instance = initialise()
        self.assertIsNotNone(instance)
        self.assertEqual(instance, BuildContext._INSTANCE)

    def test_context(self):
        initialise()
        self.assertEqual(BuildContext.context(), BuildContext._INSTANCE)
        BuildContext._INSTANCE = None

        with self.assertRaises(BuildContextError):
            BuildContext.context()

    def test_teardown(self):
        initialise()
        self.assertIsNotNone(BuildContext.context())

        teardown()

        self.assertIsNone(BuildContext._INSTANCE)


if __name__ == '__main__':
    main()
