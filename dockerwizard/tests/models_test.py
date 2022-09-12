"""
This tests the models module. For convenience, each model gets its own test case
"""
import contextlib
import unittest
from unittest.mock import Mock, patch

from .testing import main, PatchedDependencies, patch_os_path
from dockerwizard import models
from dockerwizard.errors import BuildConfigurationError

test_data = models.BuildFileData({
    'key': 'value',
    'key1': models.BuildFileData({
        'key2': 'value2'
    })
})

base_package = 'dockerwizard.models'


class StubWrapper:
    def __init__(self):
        self.value = None

    def set_value(self, value):
        self.value = value


class StubSetter:
    def process(self, build_data: models.BuildFileData, target: StubWrapper):
        target.set_value(build_data.get_property('key'))


class StubBuildFileObject(models.BuildFileObject):
    def __init__(self, tag_name: str, *properties: str):
        super().__init__(tag_name)

        for prop in properties:
            setattr(self, prop, 'value')

    def initialise(self, data: models.BuildFileData):
        pass


class BuildObjectsTest(unittest.TestCase):
    """
    Used to test BuildBileData and the base BuildFileObject
    """

    def test_build_file_data(self):
        self.assertEqual('value', test_data.get_property('key'))
        key1 = test_data.get_property('key1')
        self.assertTrue(isinstance(key1, models.BuildFileData))
        self.assertEqual('value2', key1.get_property('key2'))

        setter = StubSetter()
        target = StubWrapper()

        self.assertIsNone(target.value)

        test_data.set_properties([setter], target)

        self.assertEqual(target.value, 'value')

    def test_build_file_object(self):
        test_property = 'test_property'
        test_property1 = 'test_property_1'
        build_object = StubBuildFileObject('tag', test_property, test_property1)
        self.assertEqual('tag', build_object.tag_name)
        self.assertEqual(build_object.test_property, 'value')
        self.assertEqual(build_object.test_property_1, 'value')

        build_object.set_property(test_property, 'value1')
        build_object.set_property(test_property1, 'value2')

        self.assertEqual(build_object.test_property, 'value1')
        self.assertEqual(build_object.test_property_1, 'value2')

        with self.assertRaises(ValueError) as e:
            build_object.set_property('not_exists', 'value')

        self.assertTrue('Property not_exists is not valid' in e.exception.args)

    def test_property_setter(self):
        name = 'key'
        required = True
        validate = Mock()
        on_error = Mock()

        target = StubBuildFileObject('tag', 'key')
        setter = models.PropertySetter(name, required, validate, on_error)

        validate.return_value = None
        setter.process(test_data, target)

        validate.assert_called_with('value')
        self.assertEqual(target.key, 'value')
        validate.reset_mock()

        validate.return_value = 'Not valid'
        setter.process(test_data, target)
        validate.assert_called_with('value')
        on_error.assert_called_with('Not valid')
        validate.reset_mock()
        on_error.reset_mock()

        setter.name = 'not-found'
        setter.process(test_data, target)
        on_error.assert_called_with('not-found not found')
        on_error.reset_mock()

        setter.required = False
        setter.process(test_data, target)
        self.assertEqual(target.key, 'value')
        validate.assert_not_called()
        on_error.assert_not_called()

    def test_throw_property_error(self):
        with self.assertRaises(BuildConfigurationError) as e:
            models.throw_property_error('error')

        self.assertEqual(e.exception.message, 'error')


class FileTest(unittest.TestCase):
    def test_file(self):
        file = models.File()
        self.assertEqual('', file.path)
        self.assertTrue(file.relative_to_library)

        return_val = file.initialise(models.BuildFileData({
            'path': '/path',
            'relative_to_library': False
        }))

        self.assertEqual(return_val, file)
        self.assertEqual('/path', file.path)
        self.assertFalse(file.relative_to_library)

        with self.assertRaises(BuildConfigurationError):
            file.initialise(models.BuildFileData({
                'relative_to_library': False
            }))


class FilesTest(unittest.TestCase):
    def test_files(self):
        with patch(f'{base_package}.File') as file:
            built_file = models.File()
            file.return_value = Mock()
            file.return_value.initialise = Mock()
            file.return_value.initialise.return_value = built_file
            file_data = models.BuildFileData({
                'path': '/path',
                'relative_to_library': False
            })

            data = models.BuildFileData({
                'files': [
                    file_data
                ]
            })

            files = models.Files()
            self.assertEqual([], files.files)

            return_val = files.initialise(data)

            self.assertEqual(return_val, files)
            file.assert_called()
            file.return_value.initialise.assert_called_with(file_data)
            self.assertEqual(files.files, [built_file])

            with self.assertRaises(BuildConfigurationError) as e:
                files.initialise(models.BuildFileData({}))

            self.assertTrue('files does not exist' in e.exception.message)


class BuildStepTest(unittest.TestCase):
    def test_build_step(self):
        data = models.BuildFileData({
            'name': 'name',
            'command': 'test-command',
            'arguments': ['ls', '-l']
        })
        build_step = models.BuildStep()

        self.assertIsNone(build_step.name)
        self.assertEqual('', build_step.command)
        self.assertEqual([], build_step.arguments)

        return_val = build_step.initialise(data)

        self.assertEqual(return_val, build_step)
        self.assertEqual('name', build_step.name)
        self.assertEqual('test-command', build_step.command)
        self.assertEqual(['ls', '-l'], build_step.arguments)

        data = models.BuildFileData({
            'name': 'name',
            'arguments': ['ls', '-l']
        })

        with self.assertRaises(BuildConfigurationError):
            build_step.initialise(data)


class BuildStepsTest(unittest.TestCase):
    def test_build_steps(self):
        step = models.BuildFileData({
            'name': 'name',
            'command': 'test-command',
            'arguments': ['ls', '-l']
        })
        data = models.BuildFileData({
            'steps': [
                step
            ]
        })

        with patch(f'{base_package}.BuildStep') as buildStep:
            buildStep.return_value = Mock()
            buildStep.return_value.initialise = Mock()
            built_step = models.BuildStep()
            buildStep.return_value.initialise.return_value = built_step

            build_steps = models.BuildSteps()
            self.assertEqual([], build_steps.steps)

            return_val = build_steps.initialise(data)

            self.assertEqual(return_val, build_steps)
            self.assertEqual([built_step], build_steps.steps)
            buildStep.assert_called()
            buildStep.return_value.initialise.assert_called_with(step)

            with self.assertRaises(BuildConfigurationError) as e:
                build_steps.initialise(models.BuildFileData({}))

            self.assertTrue('steps does not exist in BuildFileData' in e.exception.message)


class DockerBuildTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self) -> PatchedDependencies:
        made_files = models.Files()
        made_files.files = [models.File()]
        made_steps = models.BuildSteps()
        made_steps.steps = [models.BuildStep()]
        dockerfile = models.File()
        dockerfile.path = 'dockerfile'

        with PatchedDependencies({
            'workdir': f'{base_package}.get_working_directory',
            'osPatch': f'{base_package}.os',
            'file': f'{base_package}.File',
            'files': f'{base_package}.Files',
            'buildStep': f'{base_package}.BuildStep',
            'buildSteps': f'{base_package}.BuildSteps',
            'pathValidator': f'{base_package}.custom_command_path_validator'
        }) as patched:
            file = patched.file
            files = patched.files
            buildSteps = patched.buildSteps
            osPatch = patched.osPatch

            file.return_value = Mock()
            file.return_value.path = 'dockerfile'
            file.return_value.initialise = Mock()
            files.return_value = Mock()
            files.return_value.initialise = Mock()
            files.return_value.initialise.return_value = made_files
            buildSteps.return_value = Mock()
            buildSteps.return_value.initialise = Mock()
            buildSteps.return_value.initialise.return_value = made_steps

            osPatch.path = patch_os_path()

            yield patched

    def test_docker_build(self):
        dockerfile = models.BuildFileData({
            'path': 'dockerfile'
        })

        data_dict = {
            'image': 'image',
            'library': 'library',
            'custom_commands': 'custom-commands.yaml',
            'dockerfile': dockerfile,
            'files': [],
            'steps': []
        }
        data = models.BuildFileData(data_dict)

        file = models.File()
        step = models.BuildStep()

        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('osPatch').path.isdir.return_value = True
            patched.get('pathValidator').return_value = None

            build = models.DockerBuild()
            self.assertEqual(build.image, '')
            self.assertIs(build.dockerfile, models.File())
            self.assertEqual(build.library, '')
            self.assertEqual(build.custom_commands, '')
            self.assertEqual(build.files, [])
            self.assertEqual(build.steps, [])

            return_val = build.initialise(data)

            self.assertEqual(return_val, build)
            self.assertEqual(build.image, 'image')
            self.assertIs(build.dockerfile.path, 'dockerfile')
            self.assertEqual(build.library, 'library')
            self.assertEqual(build.custom_commands, 'custom-commands.yaml')
            self.assertEqual(build.files[0].path, file.path)
            self.assertEqual(build.steps[0].name, step.name)

            patched.get('files').return_value.initialise.assert_called()
            patched.get('buildSteps').return_value.initialise.assert_called()

    def test_docker_build_errors(self):
        dockerfile = models.BuildFileData({
            'path': 'dockerfile'
        })

        data_dict = {
            'image': 'image',
            'library': 'library',
            'custom_commands': 'custom-commands.yaml',
            'dockerfile': dockerfile,
            'files': [],
            'steps': []
        }
        data = models.BuildFileData(data_dict)

        patched: PatchedDependencies
        with self._patch() as patched:
            build = models.DockerBuild()

            patched.get('osPatch').path.isdir.return_value = False
            patched.get('pathValidator').return_value = None

            with self.assertRaises(BuildConfigurationError) as e:
                build.initialise(data)

            self.assertTrue('not a directory' in e.exception.message)

            data_dict['dockerfile'] = None
            data = models.BuildFileData(data_dict)

            patched.get('osPatch').path.isdir.return_value = True
            with self.assertRaises(BuildConfigurationError) as e:
                build.initialise(data)

            self.assertTrue('required property' in e.exception.message)

            data_dict['dockerfile'] = dockerfile
            data = models.BuildFileData(data_dict)
            patched.get('osPatch').path.isdir.return_value = True
            patched.get('pathValidator').return_value = 'not valid'

            with self.assertRaises(BuildConfigurationError) as e:
                build.initialise(data)

            self.assertTrue('not valid' in e.exception.message)


if __name__ == '__main__':
    main()
