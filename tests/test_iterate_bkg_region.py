"""
Module for testing that iterate_uvot_reduction defers background-region
placement until a real reference image is available
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from uvotredux.download.regions import bkg_path, make_source_region
from uvotredux.uvot.iterate import iterate_uvot_reduction

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889
OBS_ID = "00019808001"


class TestIterateBkgRegion(unittest.TestCase):
    """
    Class for testing the background-region-priming step of
    iterate_uvot_reduction
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.base_dir = Path(self.tmp_dir.name)
        (self.base_dir / OBS_ID).mkdir()
        make_source_region(ra=TEST_RA, dec=TEST_DEC, base_dir=self.base_dir)

    @patch("uvotredux.uvot.iterate.parse_uvot_results")
    @patch("uvotredux.uvot.iterate.unpack_single_uvot_obs")
    @patch("uvotredux.uvot.iterate.ensure_reference_image")
    def test_creates_bkg_region_when_missing(
        self, mock_ensure_image, mock_unpack, mock_parse
    ):
        """
        When bkg.reg doesn't exist yet, a reference image should be
        obtained from the first observation and used to create it.

        :return: None
        """
        mock_ensure_image.return_value = None

        iterate_uvot_reduction(ra=TEST_RA, dec=TEST_DEC, directory=self.base_dir)

        mock_ensure_image.assert_called_once_with(self.base_dir / OBS_ID)
        self.assertTrue(bkg_path(self.base_dir).is_file())
        mock_unpack.assert_called_once()
        mock_parse.assert_called_once()

    @patch("uvotredux.uvot.iterate.parse_uvot_results")
    @patch("uvotredux.uvot.iterate.unpack_single_uvot_obs")
    @patch("uvotredux.uvot.iterate.ensure_reference_image")
    def test_skips_bkg_region_when_already_present(
        self, mock_ensure_image, _mock_unpack, _mock_parse
    ):
        """
        When bkg.reg already exists and overwrite is False, no reference
        image should be created.

        :return: None
        """
        bkg_path(self.base_dir).write_text("fk5;circle(1,1,1)\n", encoding="utf8")

        iterate_uvot_reduction(
            ra=TEST_RA, dec=TEST_DEC, directory=self.base_dir, overwrite=False
        )

        mock_ensure_image.assert_not_called()

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
        An empty directory with no observation subdirectories should raise.

        :return: None
        """
        with TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError):
                iterate_uvot_reduction(
                    ra=TEST_RA, dec=TEST_DEC, directory=Path(empty_dir)
                )


if __name__ == "__main__":
    unittest.main()
