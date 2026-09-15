"""
Module for testing automatic background-region placement that avoids
detected field sources
"""

import unittest
from unittest.mock import patch

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from uvotredux.download.regions import (
    BKG_SEPARATION,
    DEFAULT_BKG_POSITION_ANGLE,
    find_clear_background_position_angle,
)

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889
PIXEL_SCALE_DEG = 2.0 / 3600.0  # 2 arcsec/pixel
IMAGE_SIZE = 121


def _make_field_hdu(source_pa: u.Quantity | None = None) -> fits.PrimaryHDU:
    """
    Build a synthetic field image, optionally containing a bright injected
    point source at a given position angle/separation from the target.

    :param source_pa: Position angle at which to inject a fake bright
        source (at the default BKG_SEPARATION), or None for a blank field
    :return: A FITS HDU with a valid WCS
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

    return fits.PrimaryHDU(data=data, header=wcs.to_header())


class TestFindClearBackgroundPositionAngle(unittest.TestCase):
    """
    Class for testing find_clear_background_position_angle
    """

    def setUp(self):
        self.coord = SkyCoord(ra=TEST_RA, dec=TEST_DEC, unit="deg")

    @patch("astroquery.skyview.SkyView.get_images")
    def test_no_sources_keeps_default_position_angle(self, mock_get_images):
        """
        An empty field should keep the default position angle.

        :return: None
        """
        mock_get_images.return_value = [[_make_field_hdu(source_pa=None)]]

        position_angle = find_clear_background_position_angle(self.coord)

        self.assertAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )

    @patch("astroquery.skyview.SkyView.get_images")
    def test_source_at_default_position_is_avoided(self, mock_get_images):
        """
        A bright source injected exactly at the default background position
        should cause a different position angle to be chosen.

        :return: None
        """
        mock_get_images.return_value = [
            [_make_field_hdu(source_pa=DEFAULT_BKG_POSITION_ANGLE)]
        ]

        position_angle = find_clear_background_position_angle(self.coord)

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

    @patch("astroquery.skyview.SkyView.get_images")
    def test_query_failure_falls_back_to_default(self, mock_get_images):
        """
        Any failure in the underlying query should fall back to the default
        position angle rather than raising.

        :return: None
        """
        mock_get_images.side_effect = RuntimeError("network unavailable")

        position_angle = find_clear_background_position_angle(self.coord)

        self.assertAlmostEqual(
            position_angle.to_value(u.deg),  # pylint: disable=no-member
            DEFAULT_BKG_POSITION_ANGLE.to_value(u.deg),  # pylint: disable=no-member
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
