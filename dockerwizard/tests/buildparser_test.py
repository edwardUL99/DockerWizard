"""
This tests the buildparser module
"""
import contextlib
import unittest
from unittest.mock import patch, Mock

from .testing import main, PatchedDependencies
from dockerwizard import buildparser
from dockerwizard.models import DockerBuild, BuildFileData

base_package = 'dockerwizard.buildparser'


test_data = {
    'build': {
        'test': {
            'key': 'value'
        },
        'values': [
            {
                'key1': 'value1'
            }
        ]
    }
}

expected_build_file_data = BuildFileData({
    'build': BuildFileData({
        'test': BuildFileData({
            'key': 'value'
        }),
        'values': [
            BuildFileData({
                'key1': 'value1'
            })
        ]
    })
})


class BuildParserTest(unittest.TestCase):
    @contextlib.contextmanager
    def _patch(self):
        with PatchedDependencies({
            'yaml': f'{base_package}.yaml',
            'dockerBuild': f'{base_package}.DockerBuild',
            'propertyError': f'{base_package}.throw_property_error',
            'openPatch': 'builtins.open'
        }) as patched:
            patched.dockerBuild.return_value = Mock()
            patched.dockerBuild.return_value.initialise = Mock()

            yield patched

    def test_convert_dict_to_build_data(self):
        return_val = buildparser.convert_dict_to_build_data(test_data)
        self.assertTrue(isinstance(return_val, BuildFileData))

        build = return_val.get_property('build')
        self.assertTrue(isinstance(build, BuildFileData))

        test = build.get_property('test')
        self.assertTrue(isinstance(build, BuildFileData))
        self.assertEqual('value', test.get_property('key'))

        values = build.get_property('values')
        self.assertTrue(isinstance(values, list))

        value = values[0]
        self.assertTrue(isinstance(value, BuildFileData))
        self.assertEqual(value.get_property('key1'), 'value1')

    def test_yaml_build_parser(self):
        build = DockerBuild()
        patched: PatchedDependencies
        with self._patch() as patched, patch(f'{base_package}.convert_dict_to_build_data') as convert:
            patched.get('yaml').safe_load.return_value = test_data
            patched.get('dockerBuild').return_value.initialise.return_value = build

            return_val = buildparser.YamlBuildParser().parse('file.yaml')

            self.assertEqual(return_val, build)
            patched.get('yaml').safe_load.assert_called()
            convert.assert_called()

    def test_yaml_build_parser_file_not_found(self):
        patched: PatchedDependencies
        with self._patch() as patched:
            patched.get('openPatch').side_effect = FileNotFoundError()

            buildparser.YamlBuildParser().parse('file.yaml')

            patched.get('openPatch').assert_called()
            patched.get('propertyError').assert_called_with('Build Configuration File file.yaml does not exist')

    def test_get_build_parser(self):
        self.assertTrue(isinstance(buildparser.get_build_parser(), buildparser.YamlBuildParser))


if __name__ == '__main__':
    main()
