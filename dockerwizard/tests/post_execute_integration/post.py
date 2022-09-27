"""
A sample of a post verify script
"""
import it


class PostVerifyScript(it.PostVerificationTestCase):
    def __init__(self, methodName):
        super().__init__(methodName)

    def test_exists(self):
        self.assertIsNotNone(self.stdout)

        expected_outputs = [
            'Hello World from Groovy',
            'Hello World from Python',
            'image built',
            'container created'
        ]

        for out in expected_outputs:
           self.assertTrue(out in self.stdout)

        self.assertTrue(self.stderr == '')
        self.assertEqual(0, self.exit_code)


if __name__ == '__main__':
   it.main()
