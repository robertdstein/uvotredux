"""
Module to create the source region file for the Swift UVOT observations
"""

import logging
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)


def src_path(base_dir: Path) -> Path:
    """
    Function to get the path to the src.reg file

    :param base_dir: Base directory to create the region files

    :return: Path to the src.reg file
    """
    return base_dir / "src.reg"


def make_source_region(
    ra: float,
    dec: float,
    base_dir: Path | None = None,
    overwrite: bool = False,
):
    """
    Function to create the source region file for the Swift observations

    :param ra: Right Ascension in degrees
    :param dec: Declination in degrees
    :param base_dir: Base directory to create the region file
    :param overwrite: Overwrite existing file

    :return: None
    """

    if base_dir is None:
        base_dir = Path.cwd()

    src_region = src_path(base_dir)

    if src_region.is_file() and not overwrite:
        logger.info(f"Skipping, source region file already exists: {src_region}")
        return

    logger.info(f"Creating source region file: {src_region}")

    c = SkyCoord(ra=ra, dec=dec, unit="deg")
    ra_str = c.ra.to_string(unit="hour", sep=":", precision=2)
    dec_str = c.dec.to_string(unit="deg", sep=":", precision=2)
    with open(src_region, "w", encoding="utf8") as f:
        f.write(f'fk5;circle({ra_str},{dec_str},3")\n')


def load_region(
    base_dir: Path | None = None,
) -> tuple[float, float]:
    """
    Load the source region file and return the coordinates

    :param base_dir: Base directory containing region files
    :return:
    """

    if base_dir is None:
        base_dir = Path.cwd()

    src_region = src_path(base_dir)
    with open(src_region, "r", encoding="utf8") as f:
        line = f.readlines()[0]

    vals = line.split("(")[1].split(",")
    c = SkyCoord(
        ra=vals[0],
        dec=vals[1],
        unit=(u.hourangle, u.deg),  # pylint: disable=no-member
    )
    return c.ra.degree, c.dec.degree
