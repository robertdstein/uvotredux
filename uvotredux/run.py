"""
Wrapper script to run the swift reduction on a directory using command line arguments
"""

import logging
from pathlib import Path

from uvotredux.download.run import run_download
from uvotredux.uvot.iterate import iterate_uvot_reduction

logger = logging.getLogger(__name__)


def main(
    ra_deg: float,
    dec_deg: float,
    output_dir: Path,
    overwrite: bool = False,
    download: bool = True,
):
    """
    Function to run Swift UVOT reduction on a directory

    :param ra_deg: Right Ascension in degrees
    :param dec_deg: Declination in degrees
    :param output_dir: Directory to save the data
    :param overwrite: Overwrite existing files
    :param download: Whether to download the data or not
    :return: None
    """
    if download:
        run_download(
            ra_deg=ra_deg,
            dec_deg=dec_deg,
            output_dir=output_dir,
            overwrite=overwrite,
        )
    else:
        logger.info("Skipping download, assuming data is already present.")

    iterate_uvot_reduction(
        directory=output_dir,
        overwrite=overwrite,
    )
