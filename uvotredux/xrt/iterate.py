"""
Module to iterate over all the Swift UVOT observations in a directory and
unpack them
"""

import logging
from pathlib import Path

from uvotredux.utils import get_observation_dirs
from uvotredux.xrt.reduce import unpack_single_xrt_obs

logger = logging.getLogger(__name__)


def iterate_xrt_reduction(
    directory: Path | None = None,
    src_region_name: str = "src.reg",
    bkg_region_name: str = "bkg.reg",
    overwrite: bool = False,
):
    """
    Function to unpack all the swift observations in a directory

    :param directory: Directory containing the swift observations
    :param src_region_name: Path to the source region file
    :param bkg_region_name: Path to the background region file
    :param overwrite: Overwrite existing files
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

    src_region_path = directory / src_region_name
    bkg_region_path = directory / bkg_region_name

    for path in [src_region_path, bkg_region_path]:
        if not path.is_file():
            raise FileNotFoundError(f"Region file {path} not found")

    for swift_obs in sorted(all_swift_obs):
        unpack_single_xrt_obs(
            swift_obs,
            src_region_path=src_region_path,
            # bkg_region_path=bkg_region_path,
            # overwrite=overwrite,
        )

    # parse_uvot_results(directory, skyportal=skyportal)
