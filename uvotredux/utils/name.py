"""
Utility functions for assigning source names based on RA and Dec.
"""

import logging

from astropy import units as u
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)


def assign_source_name(
    ra_deg: float = None,
    dec_deg: float = None,
) -> str:
    """
    Assign a source name based on the provided RA and Dec, generating a J2000 name.

    :param ra_deg: Right Ascension in degrees
    :param dec_deg: Declination in degrees
    :return: Name
    """

    src_position = SkyCoord(ra_deg, dec_deg, unit="deg")
    ra_str = src_position.ra.to_string(
        unit=u.hour, sep="", precision=2, pad=True  # pylint: disable=no-member
    )
    dec_str = src_position.dec.to_string(
        unit=u.degree,  # pylint: disable=no-member
        sep="",
        precision=2,
        alwayssign=True,
        pad=True,
    )
    j_name = f"J{ra_str}{dec_str}"
    logger.info(f"Source name not provided. Assigning J2000 name {j_name}")
    return j_name
