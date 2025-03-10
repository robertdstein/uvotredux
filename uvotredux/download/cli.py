"""
Command line interface for the download module
"""

import argparse
import logging

from uvotredux.download.data import download_data
from uvotredux.download.regions import create_regions

logger = logging.getLogger(__name__)


def main():
    """
    Function to run the swift reduction on a directory

    :return: None
    """
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Unpack a set of Swift UVOT observation"
    )
    parser.add_argument(
        "-d", "--swift_obs_dir", help="Path to the base Swift observation directory"
    )
    parser.add_argument(
        "--ra",
        help="Right Ascension in degrees",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--dec",
        help="Declination in degrees",
        type=float,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Overwrite existing files",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    # Create src.reg and bkg.reg files, if they don't already exist
    create_regions(
        args.ra, args.dec, base_dir=args.swift_obs_dir, overwrite=args.overwrite
    )

    # Download the data
    download_data(
        ra=args.ra, dec=args.dec, overwrite=args.overwrite, directory=args.swift_obs_dir
    )
