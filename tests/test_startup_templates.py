__author__ = 'craigglennie'

import unittest

from spotmark import startup_templates

class TestStartupTemplates(unittest.TestCase):

    def test_get_startup_script(self):
        # Avoid making this a test of Jinja and just check that we inserted
        # the required AWS credentials into the script
        expected_key, expected_secret = "expected_key", "expected_secret"
        script = startup_templates.get_startup_script("base_template.sh", expected_key, expected_secret)
        self.assertTrue(expected_key in script)
        self.assertTrue(expected_secret in script)

