"""
Module for testing ensure_reference_image
"""

import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from uvotredux.uvot.reduce import ensure_reference_image

IMAGE_NAME = "sw00019808001uw2_sk.img"


class TestEnsureReferenceImage(unittest.TestCase):
    """
    Class for testing ensure_reference_image
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.obs_dir = Path(self.tmp_dir.name) / "00019808001"
        self.uvot_dir = self.obs_dir / "uvot" / "image"
        self.uvot_dir.mkdir(parents=True)

    def test_no_images_returns_none(self):
        """
        :return: None
        """
        self.assertIsNone(ensure_reference_image(self.obs_dir))

    @patch("uvotredux.uvot.reduce.execute_command")
    def test_creates_and_returns_first_image(self, mock_execute):
        """
        :return: None
        """
        (self.uvot_dir / IMAGE_NAME).touch()

        def fake_execute(
            cmd, output_path, overwrite=False
        ):  # pylint: disable=unused-argument
            output_path.touch()

        mock_execute.side_effect = fake_execute

        result = ensure_reference_image(self.obs_dir)

        self.assertIsNotNone(result)
        self.assertTrue(result.is_file())
        self.assertEqual(result.name, "UW2.fits")

    @patch("uvotredux.uvot.reduce.execute_command")
    def test_execute_command_failure_returns_none(self, mock_execute):
        """
        :return: None
        """
        (self.uvot_dir / IMAGE_NAME).touch()
        mock_execute.side_effect = subprocess.CalledProcessError(1, "uvotimsum")

        self.assertIsNone(ensure_reference_image(self.obs_dir))


if __name__ == "__main__":
    unittest.main()
