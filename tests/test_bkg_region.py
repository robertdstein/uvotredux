"""
Module for testing make_bkg_region and find_clear_background_position_angle's
fallback behaviour. (The actual source-avoidance behaviour, against a real
UVOT image, is checked in tests/test_run.py using real downloaded data.)
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from astropy import units as u
from astropy.coordinates import SkyCoord

from uvotredux.download.bkg_region import (
    DEFAULT_BKG_POSITION_ANGLE,
    bkg_path,
    find_clear_background_position_angle,
    make_bkg_region,
)

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889


class TestFindClearBackgroundPositionAngle(unittest.TestCase):
    """
    Class for testing find_clear_background_position_angle's fallback
    behaviour
    """

    def test_missing_image_falls_back_to_default(self):
        """
        A nonexistent/unreadable image should fall back to the default
        position angle rather than raising.

        :return: None
        """
        coord = SkyCoord(ra=TEST_RA, dec=TEST_DEC, unit="deg")
        position_angle = find_clear_background_position_angle(
            coord, Path("/nonexistent/path/to/image.fits")
        )

        self.assertAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )


class TestMakeBkgRegion(unittest.TestCase):
    """
    Class for testing make_bkg_region
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.base_dir = Path(self.tmp_dir.name)

    def test_without_image_falls_back_to_default(self):
        """
        With no image available, a background region should still be
        produced, using the default position.

        :return: None
        """
        make_bkg_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            image_path=None,
        )

        self.assertTrue(bkg_path(self.base_dir).is_file())

    def test_skips_when_already_exists_and_not_overwrite(self):
        """
        An existing bkg.reg should be left untouched when overwrite=False.

        :return: None
        """
        bkg_path(self.base_dir).write_text("fk5;circle(1,1,1)\n", encoding="utf8")

        make_bkg_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            overwrite=False,
        )

        self.assertEqual(
            bkg_path(self.base_dir).read_text(encoding="utf8"),
            "fk5;circle(1,1,1)\n",
        )

    def test_default_output(self):
        """
        With no image given, the background region should be at the fixed
        45 degree offset.

        :return: None
        """
        make_bkg_region(ra=TEST_RA, dec=TEST_DEC, base_dir=self.base_dir)

        content = bkg_path(self.base_dir).read_text(encoding="utf8")
        self.assertIn("16:40:21.06,26:56:08.46", content)


class TestDefaultBaseDir(unittest.TestCase):
    """
    Class for testing that make_bkg_region defaults to the current working
    directory when base_dir is not given
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self._original_cwd = Path.cwd()
        os.chdir(self.tmp_dir.name)
        self.addCleanup(os.chdir, self._original_cwd)

    def test_make_bkg_region_defaults_to_cwd(self):
        """
        :return: None
        """
        make_bkg_region(ra=TEST_RA, dec=TEST_DEC)
        self.assertTrue(bkg_path(Path.cwd()).is_file())


if __name__ == "__main__":
    unittest.main()
