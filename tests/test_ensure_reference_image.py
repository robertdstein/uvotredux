"""
Module for testing ensure_reference_image
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from uvotredux.uvot.reduce import ensure_reference_image

RAW_IMAGE_NAME = "sw00019808001uw2_sk.img"


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

    def test_returns_existing_summed_image_without_running_uvotimsum(self):
        """
        If a summed image for the observation already exists (e.g. from a
        previous run), it should be reused directly rather than re-running
        uvotimsum - this is the same caching behaviour execute_command
        already provides for every other UVOT reduction step, so it works
        even without HEASoft installed (as in this local test environment).

        :return: None
        """
        (self.uvot_dir / RAW_IMAGE_NAME).touch()
        expected_output = self.uvot_dir / "UW2.fits"
        expected_output.write_text("not a real fits file, just a marker")

        result = ensure_reference_image(self.obs_dir)

        self.assertEqual(result, expected_output)
        # Content should be untouched - uvotimsum should never have run
        self.assertEqual(
            expected_output.read_text(), "not a real fits file, just a marker"
        )


if __name__ == "__main__":
    unittest.main()
