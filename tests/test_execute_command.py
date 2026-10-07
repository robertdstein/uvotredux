"""
Module for testing where execute_command runs its commands
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from uvotredux.uvot.reduce import execute_command


class TestExecuteCommandWorkingDirectory(unittest.TestCase):
    """
    Class for testing the working directory of execute_command
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.output_dir = Path(self.tmp_dir.name) / "uvot" / "image"
        self.output_dir.mkdir(parents=True)
        self.elsewhere = Path(self.tmp_dir.name) / "elsewhere"
        self.elsewhere.mkdir()

        original_cwd = os.getcwd()
        self.addCleanup(os.chdir, original_cwd)
        os.chdir(self.elsewhere)

    def test_scratch_files_go_to_output_dir(self):
        """
        HEASoft tools (e.g. uvotimsum) write scratch files to the current
        directory, and fail if it is not writable (e.g. exit status 3,
        "unable to create template.N.M [Permission denied]"). Commands
        should run in the output directory, whatever the process cwd is.

        :return: None
        """
        output_path = self.output_dir / "UW2.fits"

        execute_command(
            cmd=f"touch scratch.tmp && touch {output_path}",
            output_path=output_path,
        )

        self.assertTrue((self.output_dir / "scratch.tmp").is_file())
        self.assertFalse((self.elsewhere / "scratch.tmp").exists())


if __name__ == "__main__":
    unittest.main()
