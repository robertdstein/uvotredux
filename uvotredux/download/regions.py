"""
Module to create region files for the Swift UVOT observations
"""

import logging
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)


def create_regions(
    ra: float,
    dec: float,
    base_dir: Path | None = None,
):
    """
    Function to create the source/background region files for the Swift  observations

    :return: None
    """

    if base_dir is None:
        base_dir = Path.cwd()

    src_region = base_dir / "src.reg"
    bkg_region = base_dir / "bkg.reg"

    if src_region.is_file():
        logger.info(f"Skipping, source region file already exists: {src_region}")
    else:
        logger.info(f"Creating source region file: {src_region}")

        c = SkyCoord(ra=ra, dec=dec, unit="deg")
        ra_str = c.ra.to_string(unit="hour", sep=":", precision=2)
        dec_str = c.dec.to_string(unit="deg", sep=":", precision=2)
        with open(src_region, "w", encoding="utf8") as f:
            f.write(f'fk5;circle({ra_str},{dec_str},3")\n')

    if bkg_region.is_file():
        logger.info(f"Skipping, background region file already exists: {bkg_region}")
    else:
        logger.info(f"Creating background region file: {bkg_region}")

        c = SkyCoord(ra=ra, dec=dec, unit="deg")

        separation = 50 * u.arcsec  # pylint: disable=no-member
        position_angle = 45 * u.deg  # pylint: disable=no-member

        c2 = c.directional_offset_by(position_angle, separation)

        ra_str = c2.ra.to_string(unit="hour", sep=":", precision=2)
        dec_str = c2.dec.to_string(unit="deg", sep=":", precision=2)

        logger.warning(
            f"Creating a background region with a radius of 10 arcseconds "
            f"and offset of {separation}, centered at {c2.ra:.5f}/{c2.dec:.5f}. "
            f"Check your images to ensure this region only contains background."
        )

        with open(bkg_region, "w", encoding="utf8") as f:
            f.write(f'fk5;circle({ra_str},{dec_str},10")\n')
