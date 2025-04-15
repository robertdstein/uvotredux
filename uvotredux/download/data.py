"""
Module to download data from the HEASARC archive.
"""

import logging
from pathlib import Path

from swifttools.swift_too import Data, ObsQuery

logger = logging.getLogger(__name__)


def download_data(
    ra: float,
    dec: float,
    overwrite: bool = False,
    directory: Path | None = None,
):
    """
    Function to download the Swift data from the HEASARC archive

    :param ra: Right Ascension in degrees
    :param dec: Declination in degrees
    :param overwrite: Overwrite existing files
    :param directory: Directory to download the data to
    :return: None
    """

    if directory is None:
        directory = Path.cwd()

    logger.info(f"Searching Swift data for {ra}, {dec}")

    oq = ObsQuery(ra=ra, dec=dec)

    if len(oq) == 0:
        logger.error("No Swift observations found")
        return

    obs_ids = set(x.obsnum for x in oq)

    logger.info(f"Found {len(obs_ids)} Swift observations")

    for obs_id in sorted(obs_ids):
        out_dir = directory / f"{obs_id}"

        if out_dir.is_dir() and not overwrite:
            logger.info(f"Skipping existing directory: {out_dir}")
            continue

        logger.info(f"Downloading Swift data for observation: {obs_id}")
        Data(obsid=obs_id, uvot=True, xrt=True, outdir=out_dir.parent, clobber=True)
