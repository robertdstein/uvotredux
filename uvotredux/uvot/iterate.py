"""
Module to iterate over all the Swift UVOT observations in a directory and unpack them
"""

import logging
from pathlib import Path

from uvotredux.download.bkg_region import bkg_path, make_bkg_region
from uvotredux.download.source_region import src_path
from uvotredux.utils import get_observation_dirs
from uvotredux.uvot.parse import parse_uvot_results
from uvotredux.uvot.reduce import ensure_reference_image, unpack_single_uvot_obs

logger = logging.getLogger(__name__)


def iterate_uvot_reduction(
    ra: float,
    dec: float,
    directory: Path | None = None,
    overwrite: bool = False,
    skyportal: bool = False,
):
    """
    Function to unpack all the swift observations in a directory

    :param ra: Right Ascension of the target in degrees
    :param dec: Declination of the target in degrees
    :param directory: Directory containing the swift observations
    :param overwrite: Overwrite existing files
    :param skyportal: Convert the results to SkyPortal format
    :return: None
    """

    if directory is None:
        directory = Path.cwd()

    directory = Path(directory)

    logger.info(f"Unpacking Swift observations in directory: {directory}")

    all_swift_obs = get_observation_dirs(directory)

    if len(all_swift_obs) == 0:
        raise FileNotFoundError(
            f"No Swift observations found in directory: {directory}"
        )

    src_region_path = src_path(directory)
    if not src_region_path.is_file():
        raise FileNotFoundError(f"Region file {src_region_path} not found")

    bkg_region_path = bkg_path(directory)
    if not bkg_region_path.is_file() or overwrite:
        # Need a real image to check for other sources before placing bkg.reg.
        reference_image = ensure_reference_image(sorted(all_swift_obs)[0])
        make_bkg_region(
            ra=ra,
            dec=dec,
            base_dir=directory,
            overwrite=overwrite,
            image_path=reference_image,
        )

    for swift_obs in sorted(all_swift_obs):
        unpack_single_uvot_obs(
            swift_obs,
            src_region_path=src_region_path,
            bkg_region_path=bkg_region_path,
            overwrite=overwrite,
        )

    parse_uvot_results(directory, skyportal=skyportal)
