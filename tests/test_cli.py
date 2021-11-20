import unittest
import os
import subprocess

from ipydex import IPS, activate_ips_on_exception
activate_ips_on_exception()



def command_with_output(cmd):

        if isinstance(cmd, str):
            cmd = cmd.split(" ") # note this breaks for spaces inside args

        assert isinstance(cmd, (list, tuple))

        res = subprocess.run(cmd, capture_output=True)
        res.stdout = res.stdout.decode("utf8")
        res.stderr = res.stderr.decode("utf8")

        return res



class TestCore(unittest.TestCase):
    def setUp(self):

        self.orig_path = os.path.abspath(os.curdir)
        os.chdir(os.path.abspath(os.path.dirname(__file__)))

    def tearDown(self):
        os.chdir(self.orig_path)

    def test_option_c(self):

        fpath = "data/knuth65.pdf"


        res = command_with_output("cp {} test.pdf".format(fpath))
        self.assertEqual(res.returncode, 0)

        res = command_with_output("pdftitle -p test.pdf -c")
        self.assertEqual(res.returncode, 0)

        title = res.stdout.strip() # remove trailing newline
        self.assertEqual(title, "on_the_translation_of_languages_from_left_to_right.pdf")
        self.assertFalse(os.path.isfile("test.pdf"))
        self.assertTrue(os.path.isfile("on_the_translation_of_languages_from_left_to_right.pdf"))

        # remove the newly created

        res = command_with_output("rm {}".format(title))
        self.assertEqual(res.returncode, 0)

