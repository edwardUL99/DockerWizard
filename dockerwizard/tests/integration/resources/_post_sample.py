"""
A sample of a post verify script
"""
import it


class PostVerifyScript(it.PostVerificationTestCase):
    def __init__(self, methodName):
        super().__init__(methodName)

    def test_exists(self):
        self.assertIsNotNone(self.stdout)
        self.assertTrue('sample output' in self.stdout)
        self.assertTrue(self.stderr == '')
        self.assertEqual(0, self.exit_code)


if __name__ == '__main__':
   it.main()
