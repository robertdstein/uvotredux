"""
Module to iterate over all the Swift UVOT observations in a directory and unpack them
"""

import logging
from pathlib import Path

from uvotredux.download.regions import bkg_path, src_path
from uvotredux.utils import get_observation_dirs
from uvotredux.uvot.parse import parse_uvot_results
from uvotredux.uvot.reduce import unpack_single_uvot_obs

logger = logging.getLogger(__name__)


def iterate_uvot_reduction(
    directory: Path | None = None,
    overwrite: bool = False,
    skyportal: bool = False,
):
    """
    Function to unpack all the swift observations in a directory

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
    bkg_region_path = bkg_path(directory)

    for path in [src_region_path, bkg_region_path]:
        if not path.is_file():
            raise FileNotFoundError(f"Region file {path} not found")

    for swift_obs in sorted(all_swift_obs):
        unpack_single_uvot_obs(
            swift_obs,
            src_region_path=src_region_path,
            bkg_region_path=bkg_region_path,
            overwrite=overwrite,
        )

    parse_uvot_results(directory, skyportal=skyportal)
