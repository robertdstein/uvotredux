"""
Module for testing automatic background-region placement that avoids
sources detected in a real UVOT image
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from uvotredux.download.regions import (
    BKG_SEPARATION,
    DEFAULT_BKG_POSITION_ANGLE,
    _candidate_position_angles,
    bkg_path,
    find_clear_background_position_angle,
    make_bkg_region,
    make_source_region,
    src_path,
)

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889
PIXEL_SCALE_DEG = 2.0 / 3600.0  # 2 arcsec/pixel
IMAGE_SIZE = 121


def _make_field_image(path: Path, source_pa: u.Quantity | None = None) -> None:
    """
    Write a synthetic UVOT-like image to `path`, optionally containing a
    bright injected point source at a given position angle/separation from
    the target.

    :param path: Where to write the FITS file
    :param source_pa: Position angle at which to inject a fake bright
        source (at the default BKG_SEPARATION), or None for a blank field
    :return: None
    """
    crpix = IMAGE_SIZE // 2 + 1

    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [crpix, crpix]
    wcs.wcs.cdelt = [-PIXEL_SCALE_DEG, PIXEL_SCALE_DEG]
    wcs.wcs.crval = [TEST_RA, TEST_DEC]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    rng = np.random.default_rng(42)
    data = rng.normal(loc=100.0, scale=2.0, size=(IMAGE_SIZE, IMAGE_SIZE))

    if source_pa is not None:
        coord = SkyCoord(ra=TEST_RA, dec=TEST_DEC, unit="deg")
        target = coord.directional_offset_by(source_pa, BKG_SEPARATION)
        x0, y0 = wcs.world_to_pixel(target)

        yy, xx = np.mgrid[0:IMAGE_SIZE, 0:IMAGE_SIZE]
        sigma = 2.0
        data += 500.0 * np.exp(-(((xx - x0) ** 2 + (yy - y0) ** 2) / (2 * sigma**2)))

    fits.PrimaryHDU(data=data, header=wcs.to_header()).writeto(path, overwrite=True)


class TestFindClearBackgroundPositionAngle(unittest.TestCase):
    """
    Class for testing find_clear_background_position_angle, run against a
    real (synthetic) local FITS file - no network calls involved.
    """

    def setUp(self):
        self.coord = SkyCoord(ra=TEST_RA, dec=TEST_DEC, unit="deg")
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.image_path = Path(self.tmp_dir.name) / "image.fits"

    def test_no_sources_keeps_default_position_angle(self):
        """
        An empty field should keep the default position angle.

        :return: None
        """
        _make_field_image(self.image_path, source_pa=None)

        position_angle = find_clear_background_position_angle(
            self.coord, self.image_path
        )

        self.assertAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )

    def test_source_at_default_position_is_avoided(self):
        """
        A bright source injected exactly at the default background position
        should cause a different position angle to be chosen.

        :return: None
        """
        _make_field_image(self.image_path, source_pa=DEFAULT_BKG_POSITION_ANGLE)

        position_angle = find_clear_background_position_angle(
            self.coord, self.image_path
        )

        self.assertNotAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )

        # The chosen position should actually be clear of the injected source
        candidate = self.coord.directional_offset_by(position_angle, BKG_SEPARATION)
        source = self.coord.directional_offset_by(
            DEFAULT_BKG_POSITION_ANGLE, BKG_SEPARATION
        )
        separation_arcsec = candidate.separation(source).to_value(
            u.arcsec  # pylint: disable=no-member
        )
        self.assertGreater(separation_arcsec, 15.0)

    def test_sources_at_every_candidate_falls_back_to_least_crowded(self):
        """
        If every candidate position angle is blocked, the function should
        still return its best (least-crowded) option rather than raising.

        :return: None
        """
        crpix = IMAGE_SIZE // 2 + 1
        wcs = WCS(naxis=2)
        wcs.wcs.crpix = [crpix, crpix]
        wcs.wcs.cdelt = [-PIXEL_SCALE_DEG, PIXEL_SCALE_DEG]
        wcs.wcs.crval = [TEST_RA, TEST_DEC]
        wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        rng = np.random.default_rng(7)
        data = rng.normal(loc=100.0, scale=2.0, size=(IMAGE_SIZE, IMAGE_SIZE))

        # Inject a source at every candidate position angle itself, so
        # every candidate is blocked and none can clear the avoidance radius.
        yy, xx = np.mgrid[0:IMAGE_SIZE, 0:IMAGE_SIZE]
        for position_angle in _candidate_position_angles():
            target = self.coord.directional_offset_by(position_angle, BKG_SEPARATION)
            x0, y0 = wcs.world_to_pixel(target)
            data += 500.0 * np.exp(-(((xx - x0) ** 2 + (yy - y0) ** 2) / (2 * 2.0**2)))

        fits.PrimaryHDU(data=data, header=wcs.to_header()).writeto(
            self.image_path, overwrite=True
        )

        # Should log the "could not find a clear position" fallback and
        # still return a position angle, not raise
        with self.assertLogs("uvotredux.download.regions", level="WARNING") as logs:
            position_angle = find_clear_background_position_angle(
                self.coord, self.image_path
            )
        self.assertIsInstance(position_angle, u.Quantity)
        self.assertTrue(
            any("least crowded option" in message for message in logs.output)
        )

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


class TestMakeBkgRegion(unittest.TestCase):
    """
    Class for testing make_bkg_region
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.base_dir = Path(self.tmp_dir.name)

    def test_avoid_sources_without_image_falls_back_to_default(self):
        """
        avoid_sources=True with no image available should still produce a
        background region, using the default position.

        :return: None
        """
        make_bkg_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            avoid_sources=True,
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

    def test_default_output_unchanged_with_avoid_sources_false(self):
        """
        The default (avoid_sources=False) behaviour should be exactly the
        fixed 45 degree offset, regardless of any image passed in.

        :return: None
        """
        image_path = self.base_dir / "image.fits"
        _make_field_image(image_path, source_pa=DEFAULT_BKG_POSITION_ANGLE)

        make_bkg_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            avoid_sources=False,
            image_path=image_path,
        )

        content = bkg_path(self.base_dir).read_text(encoding="utf8")
        self.assertIn("16:40:21.06,26:56:08.46", content)

    def test_avoid_sources_true_changes_output_when_blocked(self):
        """
        With avoid_sources=True and a source blocking the default position,
        the written region should differ from the default-position output.

        :return: None
        """
        image_path = self.base_dir / "image.fits"
        _make_field_image(image_path, source_pa=DEFAULT_BKG_POSITION_ANGLE)

        make_bkg_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            avoid_sources=True,
            image_path=image_path,
        )

        content = bkg_path(self.base_dir).read_text(encoding="utf8")
        self.assertNotIn("16:40:21.06,26:56:08.46", content)


class TestDefaultBaseDir(unittest.TestCase):
    """
    Class for testing that make_source_region/make_bkg_region default to
    the current working directory when base_dir is not given
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self._original_cwd = Path.cwd()
        os.chdir(self.tmp_dir.name)
        self.addCleanup(os.chdir, self._original_cwd)

    def test_make_source_region_defaults_to_cwd(self):
        """
        :return: None
        """
        make_source_region(ra=TEST_RA, dec=TEST_DEC)
        self.assertTrue(src_path(Path.cwd()).is_file())

    def test_make_bkg_region_defaults_to_cwd(self):
        """
        :return: None
        """
        make_bkg_region(ra=TEST_RA, dec=TEST_DEC)
        self.assertTrue(bkg_path(Path.cwd()).is_file())


if __name__ == "__main__":
    unittest.main()
