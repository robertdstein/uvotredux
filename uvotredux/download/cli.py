"""
Command line interface for the download module
"""

# pylint: disable=duplicate-code
import argparse
import logging

from uvotredux.download.data import download_data
from uvotredux.download.regions import create_regions, load_region
from uvotredux.utils.tns import get_tns_by_name

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
        "-n",
        "--name",
        help="Name of the source (e.g. AT2020mni). "
        "If not provided, the RA and DEC must be specified.",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--ra",
        help="Right Ascension in degrees",
        type=float,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--dec",
        help="Declination in degrees",
        type=float,
        required=False,
        default=None,
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Overwrite existing files",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    if (args.ra is None) | (args.dec is None):
        try:
            args.ra, args.dec = load_region(base_dir=args.swift_obs_dir)
        except FileNotFoundError:
            if args.name is not None:
                # If the name is provided, get the coordinates from TNS
                tns_data = get_tns_by_name(
                    args.name, output_dir=args.swift_obs_dir, use_cache=False
                )
                args.ra, args.dec = tns_data["ra"], tns_data["dec"]
            else:
                raise

    # Create src.reg and bkg.reg files, if they don't already exist
    create_regions(
        args.ra, args.dec, base_dir=args.swift_obs_dir, overwrite=args.overwrite
    )

    # Download the data
    download_data(
        ra=args.ra, dec=args.dec, overwrite=args.overwrite, directory=args.swift_obs_dir
    )
