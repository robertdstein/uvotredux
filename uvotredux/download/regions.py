"""
Module to create region files for the Swift UVOT observations
"""

import logging
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord

logger = logging.getLogger(__name__)

# Defaults for the background region: a fixed offset from the source,
# at a 45 degree position angle.
BKG_SEPARATION = 50 * u.arcsec  # pylint: disable=no-member
BKG_RADIUS = 10 * u.arcsec  # pylint: disable=no-member
DEFAULT_BKG_POSITION_ANGLE = 45 * u.deg  # pylint: disable=no-member

# How far a candidate background aperture must be from any detected field
# source to be considered "clear" of it.
SOURCE_AVOIDANCE_RADIUS = 15 * u.arcsec  # pylint: disable=no-member

# Size of the reference field image fetched for source detection.
FIELD_CUTOUT_SIZE = 6 * u.arcmin  # pylint: disable=no-member

# Position angles are tried in steps of this size, spiralling outwards from
# DEFAULT_BKG_POSITION_ANGLE, until a clear one is found.
POSITION_ANGLE_STEP = 15 * u.deg  # pylint: disable=no-member


def src_path(base_dir: Path) -> Path:
    """
    Function to get the path to the src.reg file

    :param base_dir: Base directory to create the region files

    :return: Path to the src.reg file
    """
    return base_dir / "src.reg"


def bkg_path(base_dir: Path) -> Path:
    """
    Function to get the path to the bkg.reg file

    :param base_dir: Base directory to create the region files

    :return: Path to the bkg.reg file
    """
    return base_dir / "bkg.reg"


def _detect_field_sources(  # pylint: disable=too-many-locals
    coord: SkyCoord,
) -> SkyCoord | None:
    """
    Fetch a DSS cutout of the field around `coord` and run source detection
    on it.

    :param coord: Sky position of the target

    :return: Sky positions of detected sources, or None if detection was
        unavailable, failed, or found nothing
    """
    try:
        # Imports are local: astroquery/photutils are optional dependencies,
        # only required for this (opt-in) feature.
        # pylint: disable=import-outside-toplevel
        from astropy.stats import sigma_clipped_stats
        from astropy.wcs import WCS
        from astroquery.skyview import SkyView
        from photutils.detection import DAOStarFinder

        images = SkyView.get_images(
            position=coord,
            survey=["DSS2 Blue"],
            width=FIELD_CUTOUT_SIZE,
            height=FIELD_CUTOUT_SIZE,
        )
        hdu = images[0][0]
        wcs = WCS(hdu.header)
        data = hdu.data.astype(float)

        _, median, std = sigma_clipped_stats(data, sigma=3.0)
        finder = DAOStarFinder(threshold=5.0 * std, fwhm=3.0)
        sources = finder(data - median)

        if sources is None or len(sources) == 0:
            logger.info(
                "No field sources detected; using the default background position."
            )
            return None

        x_col = "x_centroid" if "x_centroid" in sources.colnames else "xcentroid"
        y_col = "y_centroid" if "y_centroid" in sources.colnames else "ycentroid"
        return wcs.pixel_to_world(sources[x_col], sources[y_col])

    except Exception as e:  # pylint: disable=broad-except
        logger.warning(
            f"Could not run field source detection ({e}); "
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


def find_clear_background_position_angle(coord: SkyCoord) -> u.Quantity:
    """
    Try to find a position angle, at a fixed separation (BKG_SEPARATION) from
    `coord`, whose background aperture avoids known field sources. Sources
    are found by running source detection on a DSS cutout of the field.

    This is a best-effort enhancement: if source detection is unavailable or
    fails for any reason (missing optional dependency, network error, no
    cutout available, etc.), it logs a warning and falls back to
    DEFAULT_BKG_POSITION_ANGLE.

    :param coord: Sky position of the target

    :return: Position angle to use for the background region
    """
    source_coords = _detect_field_sources(coord)
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
                f"(nearest at {min_sep:.1f})."
            )
            return position_angle

    logger.warning(
        f"Could not find a background position fully clear of "
        f"{len(source_coords)} detected field source(s); using the least "
        f"crowded option (PA={best_pa:.1f}, nearest source at {best_min_sep:.1f})."
    )
    return best_pa


def create_regions(
    ra: float,
    dec: float,
    base_dir: Path | None = None,
    overwrite: bool = False,
    avoid_sources: bool = False,
):
    """
    Function to create the source/background region files for the Swift  observations

    :param ra: Right Ascension in degrees
    :param dec: Declination in degrees
    :param base_dir: Base directory to create the region files
    :param overwrite: Overwrite existing files
    :param avoid_sources: Try to automatically place the background region
        away from other detected sources in the field, using a DSS cutout
        of the field (requires the optional astroquery/photutils
        dependencies; falls back to the default fixed position on failure)

    :return: None
    """

    if base_dir is None:
        base_dir = Path.cwd()

    src_region = src_path(base_dir)
    bkg_region = bkg_path(base_dir)

    if src_region.is_file() and not overwrite:
        logger.info(f"Skipping, source region file already exists: {src_region}")
    else:
        logger.info(f"Creating source region file: {src_region}")

        c = SkyCoord(ra=ra, dec=dec, unit="deg")
        ra_str = c.ra.to_string(unit="hour", sep=":", precision=2)
        dec_str = c.dec.to_string(unit="deg", sep=":", precision=2)
        with open(src_region, "w", encoding="utf8") as f:
            f.write(f'fk5;circle({ra_str},{dec_str},3")\n')

    if bkg_region.is_file() and not overwrite:
        logger.info(f"Skipping, background region file already exists: {bkg_region}")
    else:
        logger.info(f"Creating background region file: {bkg_region}")

        c = SkyCoord(ra=ra, dec=dec, unit="deg")

        if avoid_sources:
            position_angle = find_clear_background_position_angle(c)
        else:
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
