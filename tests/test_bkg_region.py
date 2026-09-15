"""
Module for testing make_bkg_region and find_clear_background_position_angle's
fallback behaviour. (The actual source-avoidance behaviour, against a real
UVOT image, is checked in tests/test_run.py using real downloaded data.)
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits

from uvotredux.download.bkg_region import (
    BKG_SEPARATION,
    DEFAULT_BKG_POSITION_ANGLE,
    SOURCE_AVOIDANCE_RADIUS,
    _candidate_position_angles,
    _detect_sources_in_image,
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

    def setUp(self):
        self.coord = SkyCoord(ra=TEST_RA, dec=TEST_DEC, unit="deg")

    def test_missing_image_falls_back_to_default(self):
        """
        A nonexistent/unreadable image should fall back to the default
        position angle rather than raising.

        :return: None
        """
        position_angle = find_clear_background_position_angle(
            self.coord, Path("/nonexistent/path/to/image.fits")
        )

        self.assertAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )

    # The two tests below mock _detect_sources_in_image rather than pointing
    # it at a real image, because they need to control exactly which sky
    # positions come back as "detected sources" - something no single real
    # UVOT exposure can be relied on to provide on demand (tests/test_run.py
    # already exercises this function for real, against a genuine UVOT
    # image, but that real field happens to leave the default position
    # clear - there's no real fixture available where it doesn't).

    @patch("uvotredux.download.bkg_region._detect_sources_in_image")
    def test_source_blocking_default_is_avoided(self, mock_detect):
        """
        A source at exactly the default background position should cause a
        different position angle to be chosen.

        Mocked: this requires a detected source at one exact sky position
        (the default candidate), which isn't something a real exposure can
        be made to guarantee.

        :return: None
        """
        blocked_source = self.coord.directional_offset_by(
            DEFAULT_BKG_POSITION_ANGLE, BKG_SEPARATION
        )
        mock_detect.return_value = SkyCoord([blocked_source.ra], [blocked_source.dec])

        position_angle = find_clear_background_position_angle(
            self.coord, Path("/irrelevant/since/detection/is/mocked.fits")
        )

        self.assertNotAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )

        candidate = self.coord.directional_offset_by(position_angle, BKG_SEPARATION)
        self.assertGreaterEqual(
            candidate.separation(blocked_source), SOURCE_AVOIDANCE_RADIUS
        )

    @patch("uvotredux.download.bkg_region._detect_sources_in_image")
    def test_every_candidate_blocked_returns_least_crowded(self, mock_detect):
        """
        If every candidate position angle has a source on it, the function
        should still return its best (least-crowded) option rather than
        raising.

        Mocked: this requires a detected source at every one of the ~25
        candidate directions simultaneously, which no real exposure could
        ever provide - the whole point of the feature is to find a
        direction with fewer sources than the others.

        :return: None
        """
        blocked_sources = SkyCoord(
            [
                self.coord.directional_offset_by(pa, BKG_SEPARATION)
                for pa in _candidate_position_angles()
            ]
        )
        mock_detect.return_value = blocked_sources

        with self.assertLogs("uvotredux.download.bkg_region", level="WARNING") as logs:
            position_angle = find_clear_background_position_angle(
                self.coord, Path("/irrelevant/since/detection/is/mocked.fits")
            )

        self.assertIsInstance(position_angle, u.Quantity)  # pylint: disable=no-member
        self.assertTrue(
            any("least crowded option" in message for message in logs.output)
        )


class TestDetectSourcesInImage(unittest.TestCase):
    """
    Class for testing _detect_sources_in_image's error handling on genuinely
    real (if deliberately unusual) FITS input - no mocking needed, since a
    real data-less FITS file is easy to construct directly.
    """

    def test_data_less_fits_file_returns_none(self):
        """
        A valid FITS file with no HDU containing image data should be
        handled gracefully (the StopIteration case), not raise.

        :return: None
        """
        with TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "empty.fits"
            fits.PrimaryHDU(data=None).writeto(image_path)

            self.assertIsNone(_detect_sources_in_image(image_path))


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
