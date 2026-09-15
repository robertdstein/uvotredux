"""
Command line interface for the download module
"""

import logging
from pathlib import Path

from uvotredux.download.data import download_data
from uvotredux.download.regions import make_source_region

logger = logging.getLogger(__name__)


def run_download(
    ra_deg: float,
    dec_deg: float,
    output_dir: Path,
    overwrite: bool = False,
):
    """
    Function to download Swift data and create the source region file.

    The background region is created later, once real image data is
    available to check for other sources in the field (see
    uvotredux.uvot.iterate.iterate_uvot_reduction).

    :param ra_deg: Right Ascension in degrees
    :param dec_deg: Declination in degrees
    :param output_dir: Directory to save the data
    :param overwrite: Overwrite existing files
    :return: None
    """

    # Create src.reg, if it doesn't already exist
    make_source_region(
        ra=ra_deg,
        dec=dec_deg,
        base_dir=output_dir,
        overwrite=overwrite,
    )

    # Download the data
    download_data(ra=ra_deg, dec=dec_deg, overwrite=overwrite, directory=output_dir)
