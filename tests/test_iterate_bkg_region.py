"""
Module for testing that iterate_uvot_reduction defers background-region
placement until a real reference image is available
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from uvotredux.download.regions import bkg_path, make_source_region
from uvotredux.uvot.iterate import iterate_uvot_reduction

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889
OBS_ID = "00019808001"


class TestIterateBkgRegion(unittest.TestCase):
    """
    Class for testing the background-region-priming step of
    iterate_uvot_reduction. The observation directory here deliberately has
    no real UVOT images in it - iterate_uvot_reduction still needs to raise
    (via parse_uvot_results finding nothing to parse), but bkg.reg should
    already have been created for real, from the priming step, before that
    happens.
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.base_dir = Path(self.tmp_dir.name)
        (self.base_dir / OBS_ID / "uvot" / "image").mkdir(parents=True)
        make_source_region(ra=TEST_RA, dec=TEST_DEC, base_dir=self.base_dir)

    def test_creates_bkg_region_when_missing(self):
        """
        When bkg.reg doesn't exist yet, it should be created (falling back
        to the default position, since there are no real images here to
        detect sources in) before the (expected) downstream failure.

        :return: None
        """
        with self.assertRaises(FileNotFoundError):
            iterate_uvot_reduction(ra=TEST_RA, dec=TEST_DEC, directory=self.base_dir)

        self.assertTrue(bkg_path(self.base_dir).is_file())

    def test_skips_bkg_region_when_already_present(self):
        """
        When bkg.reg already exists and overwrite is False, it should be
        left untouched.

        :return: None
        """
        bkg_path(self.base_dir).write_text("fk5;circle(1,1,1)\n", encoding="utf8")

        with self.assertRaises(FileNotFoundError):
            iterate_uvot_reduction(
                ra=TEST_RA, dec=TEST_DEC, directory=self.base_dir, overwrite=False
            )

        self.assertEqual(
            bkg_path(self.base_dir).read_text(encoding="utf8"),
            "fk5;circle(1,1,1)\n",
        )

    def test_missing_source_region_raises(self):
        """
        A missing src.reg should raise, since it should always have been
        created before any reduction runs.

        :return: None
        """
        bkg_path(self.base_dir).write_text("fk5;circle(1,1,1)\n", encoding="utf8")
        src_region = self.base_dir / "src.reg"
        src_region.unlink()

        with self.assertRaises(FileNotFoundError):
            iterate_uvot_reduction(ra=TEST_RA, dec=TEST_DEC, directory=self.base_dir)

    def test_no_observations_raises(self):
        """
        A directory with no observation subdirectories should raise.

        :return: None
        """
        with TemporaryDirectory() as empty_dir:
            make_source_region(ra=TEST_RA, dec=TEST_DEC, base_dir=Path(empty_dir))
            with self.assertRaises(FileNotFoundError):
                iterate_uvot_reduction(
                    ra=TEST_RA, dec=TEST_DEC, directory=Path(empty_dir)
                )


if __name__ == "__main__":
    unittest.main()
