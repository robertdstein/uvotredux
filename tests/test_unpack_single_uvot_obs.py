"""
Module for testing that grism images are skipped, not crashed on
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from uvotredux.uvot.filters import get_uvot_filter
from uvotredux.uvot.reduce import unpack_single_uvot_obs

# Real Swift UVOT filenames from AT2019qiz/00012012006, an observation
# with a V-grism exposure alongside a UW1 image - this originally crashed
# reduction with KeyError: 'gv'.
GRISM_IMAGE_NAME = "sw00012012006ugv_sk.img"
UW1_IMAGE_NAME = "sw00012012006uw1_sk.img"


class TestGetUvotFilter(unittest.TestCase):
    """
    Class for testing get_uvot_filter
    """

    def test_recognises_imaging_filters(self):
        """
        :return: None
        """
        self.assertEqual(get_uvot_filter(Path(UW1_IMAGE_NAME)), "UW1")

    def test_returns_none_for_grism(self):
        """
        Grism exposures (UV grism "ugu", V grism "ugv") have no entry in
        filter_dict - get_uvot_filter should report this rather than
        raising, so callers can skip them.

        :return: None
        """
        self.assertIsNone(get_uvot_filter(Path(GRISM_IMAGE_NAME)))
        self.assertIsNone(get_uvot_filter(Path("sw00012012006ugu_sk.img")))


class TestUnpackSingleUvotObsSkipsGrism(unittest.TestCase):
    """
    Class for testing that unpack_single_uvot_obs skips grism images
    instead of crashing
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.obs_dir = Path(self.tmp_dir.name) / "00012012006"
        self.uvot_dir = self.obs_dir / "uvot" / "image"
        self.uvot_dir.mkdir(parents=True)
        (self.uvot_dir / GRISM_IMAGE_NAME).touch()
        (self.uvot_dir / UW1_IMAGE_NAME).touch()

    def test_grism_image_is_skipped_not_raised(self):
        """
        Reproduces the AT2019qiz/00012012006 crash (KeyError: 'gv') - the
        grism image should be skipped with a warning, and the real
        imaging filter alongside it should still be attempted.

        :return: None
        """
        with self.assertLogs("uvotredux.uvot.reduce", level="WARNING") as log:
            # Should not raise, even without HEASoft installed
            unpack_single_uvot_obs(
                self.obs_dir,
                src_region_path=self.uvot_dir / "src.reg",
                bkg_region_path=self.uvot_dir / "bkg.reg",
            )

        self.assertTrue(any("grism" in message.lower() for message in log.output))
        # The grism image has no filter name, so no output file for it
        self.assertFalse((self.uvot_dir / "None.fits").exists())


if __name__ == "__main__":
    unittest.main()
