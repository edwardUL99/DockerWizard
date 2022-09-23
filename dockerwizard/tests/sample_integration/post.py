"""
A sample of a post verify script
"""
import it


class PostVerifyScript(it.PostVerificationTestCase):
    def __init__(self, methodName):
        super().__init__(methodName)

    def test_stdout(self):
        self.assertIsNotNone(self.stdout)
        self.assertTrue(self.stderr == '')
        self.assertEqual(0, self.exit_code)

        with open('expected_output.txt', 'r') as f:
            self.assertEqual(f.read(), self.stdout)

    def test_environment_variables(self):
        environ = self.read_program_envs('docker')

        self.assertIsNotNone(environ)
        self.assertEqual(environ['MESSAGE'], 'Hello World from the sample DockerBuild build file')
        self.assertEqual(environ['key1'], 'this is a value')
        self.assertEqual(environ['key2'], 'this is another value')


if __name__ == '__main__':
   it.main()
