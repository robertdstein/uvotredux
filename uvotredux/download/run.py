"""
Command line interface for the download module
"""

import logging
from pathlib import Path

from uvotredux.download.data import download_data
from uvotredux.download.regions import create_regions

logger = logging.getLogger(__name__)


def run_download(
    ra_deg: float,
    dec_deg: float,
    output_dir: Path,
    overwrite: bool = False,
    avoid_sources: bool = False,
):
    """
    Function to download Swift data and create region files.

    :param ra_deg: Right Ascension in degrees
    :param dec_deg: Declination in degrees
    :param output_dir: Directory to save the data
    :param overwrite: Overwrite existing files
    :param avoid_sources: Try to automatically place the background region
        away from other detected sources in the field
    :return: None
    """

    # Create src.reg and bkg.reg files, if they don't already exist
    create_regions(
        ra=ra_deg,
        dec=dec_deg,
        base_dir=output_dir,
        overwrite=overwrite,
        avoid_sources=avoid_sources,
    )

    # Download the data
    download_data(ra=ra_deg, dec=dec_deg, overwrite=overwrite, directory=output_dir)
