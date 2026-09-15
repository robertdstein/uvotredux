"""
Module to create the background region file for the Swift UVOT observations
"""

import logging
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.wcs import WCS
from photutils.detection import DAOStarFinder

logger = logging.getLogger(__name__)

# Defaults for the background region: a fixed offset from the source,
# at a 45 degree position angle.
BKG_SEPARATION = 50 * u.arcsec  # pylint: disable=no-member
BKG_RADIUS = 10 * u.arcsec  # pylint: disable=no-member
DEFAULT_BKG_POSITION_ANGLE = 45 * u.deg  # pylint: disable=no-member

# How far a candidate background aperture must be from any detected field
# source to be considered "clear" of it.
SOURCE_AVOIDANCE_RADIUS = 15 * u.arcsec  # pylint: disable=no-member

# Position angles are tried in steps of this size, spiralling outwards from
# DEFAULT_BKG_POSITION_ANGLE, until a clear one is found.
POSITION_ANGLE_STEP = 15 * u.deg  # pylint: disable=no-member


def bkg_path(base_dir: Path) -> Path:
    """
    Function to get the path to the bkg.reg file

    :param base_dir: Base directory to create the region files

    :return: Path to the bkg.reg file
    """
    return base_dir / "bkg.reg"


def _detect_sources_in_image(image_path: Path) -> SkyCoord | None:
    """
    Run source detection on a real UVOT image, so the background region can
    be placed to avoid other sources visible in that same filter/field.

    :param image_path: Path to a summed UVOT image (e.g. produced by
        uvotimsum), with a valid WCS

    :return: Sky positions of detected sources, or None if detection
        failed or found nothing
    """
    try:
        with fits.open(image_path) as hdul:
            hdu = next(h for h in hdul if h.data is not None)
            wcs = WCS(hdu.header)
            data = hdu.data.astype(float)

        _, median, std = sigma_clipped_stats(data, sigma=3.0)
        finder = DAOStarFinder(threshold=5.0 * std, fwhm=3.0)
        sources = finder(data - median)

        if sources is None or len(sources) == 0:
            logger.info(
                "No field sources detected in the reference image; "
                "using the default background position."
            )
            return None

        x_col = "x_centroid" if "x_centroid" in sources.colnames else "xcentroid"
        y_col = "y_centroid" if "y_centroid" in sources.colnames else "ycentroid"
        return wcs.pixel_to_world(sources[x_col], sources[y_col])

    except Exception as e:  # pylint: disable=broad-except
        logger.warning(
            f"Could not run field source detection on {image_path} ({e}); "
            f"falling back to the default background position."
        )
        return None


def _candidate_position_angles() -> list[u.Quantity]:
    """
    Position angles to try, starting at DEFAULT_BKG_POSITION_ANGLE and
    spiralling outwards in steps of POSITION_ANGLE_STEP.

    :return: List of candidate position angles
    """
    angles = [DEFAULT_BKG_POSITION_ANGLE]
    n_steps = int(180 / POSITION_ANGLE_STEP.value)
    for step in range(1, n_steps + 1):
        angles.append(DEFAULT_BKG_POSITION_ANGLE + step * POSITION_ANGLE_STEP)
        angles.append(DEFAULT_BKG_POSITION_ANGLE - step * POSITION_ANGLE_STEP)
    return angles


def find_clear_background_position_angle(
    coord: SkyCoord, image_path: Path
) -> u.Quantity:
    """
    Try to find a position angle, at a fixed separation (BKG_SEPARATION) from
    `coord`, whose background aperture avoids other sources detected in a
    real UVOT image of the field.

    This is a best-effort enhancement: if source detection fails for any
    reason (unreadable image, no WCS, etc.), it logs a warning and falls
    back to DEFAULT_BKG_POSITION_ANGLE.

    :param coord: Sky position of the target
    :param image_path: Path to a summed UVOT image of the field

    :return: Position angle to use for the background region
    """
    source_coords = _detect_sources_in_image(image_path)
    if source_coords is None:
        return DEFAULT_BKG_POSITION_ANGLE

    worst_separation = -1 * u.arcsec  # pylint: disable=no-member
    best_pa, best_min_sep = DEFAULT_BKG_POSITION_ANGLE, worst_separation
    for position_angle in _candidate_position_angles():
        candidate = coord.directional_offset_by(position_angle, BKG_SEPARATION)
        min_sep = candidate.separation(source_coords).min()

        if min_sep > best_min_sep:
            best_pa, best_min_sep = position_angle, min_sep

        if min_sep >= SOURCE_AVOIDANCE_RADIUS:
            logger.info(
                f"Found a background position at PA={position_angle:.1f} clear of "
                f"{len(source_coords)} detected field source(s) "
                f"(nearest at {min_sep.to(u.arcsec):.1f})."  # pylint: disable=no-member
            )
            return position_angle

    logger.warning(
        f"Could not find a background position fully clear of "
        f"{len(source_coords)} detected field source(s); using the least "
        f"crowded option (PA={best_pa:.1f}, nearest source at "
        f"{best_min_sep.to(u.arcsec):.1f})."  # pylint: disable=no-member
    )
    return best_pa


def make_bkg_region(
    ra: float,
    dec: float,
    base_dir: Path | None = None,
    overwrite: bool = False,
    image_path: Path | None = None,
):
    """
    Function to create the background region file for the Swift observations.

    By default, the background region is automatically placed away from
    other sources detected in `image_path`, falling back to a fixed offset
    if no image is given or if detection fails. If a background region file
    already exists and overwrite is False, it is left untouched.

    :param ra: Right Ascension in degrees
    :param dec: Declination in degrees
    :param base_dir: Base directory to create the region file
    :param overwrite: Overwrite existing file
    :param image_path: Path to a real UVOT image of the field, used to
        detect other sources to avoid

    :return: None
    """

    if base_dir is None:
        base_dir = Path.cwd()

    bkg_region = bkg_path(base_dir)

    if bkg_region.is_file() and not overwrite:
        logger.info(f"Skipping, background region file already exists: {bkg_region}")
        return

    logger.info(f"Creating background region file: {bkg_region}")

    c = SkyCoord(ra=ra, dec=dec, unit="deg")

    if image_path is not None:
        position_angle = find_clear_background_position_angle(c, image_path)
    else:
        logger.warning(
            "No reference image available to check for field sources; "
            "using the default background position."
        )
        position_angle = DEFAULT_BKG_POSITION_ANGLE

    c2 = c.directional_offset_by(position_angle, BKG_SEPARATION)

    ra_str = c2.ra.to_string(unit="hour", sep=":", precision=2)
    dec_str = c2.dec.to_string(unit="deg", sep=":", precision=2)

    logger.warning(
        f"Creating a background region with a radius of {BKG_RADIUS} "
        f"and offset of {BKG_SEPARATION}, centered at "
        f"{c2.ra:.5f}/{c2.dec:.5f}. Check your images to ensure this "
        f"region only contains background."
    )

    bkg_radius_arcsec = BKG_RADIUS.to_value(u.arcsec)  # pylint: disable=no-member
    with open(bkg_region, "w", encoding="utf8") as f:
        f.write(f'fk5;circle({ra_str},{dec_str},{bkg_radius_arcsec:.0f}")\n')
