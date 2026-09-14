"""
Module to download data from the HEASARC archive.
"""

import logging
from pathlib import Path

from swifttools.swift_too import Data, ObsQuery

from uvotredux.download.exceptions import SwiftAPIError

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

    if not oq.status:
        error_detail = (
            "; ".join(oq.status.errors) if oq.status.errors else oq.status.status
        ).rstrip(".")
        logger.error(f"Swift observation query failed: {error_detail}")
        raise SwiftAPIError(
            f"Swift observation query failed (status={oq.status.status}): "
            f"{error_detail}. The Swift TOO API may be temporarily "
            "unavailable - please try again later."
        )

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
        Data(
            obsid=obs_id, uvot=True, xrt=True, outdir=str(out_dir.parent), clobber=True
        )
