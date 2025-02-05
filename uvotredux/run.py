"""
Wrapper script to run the swift reduction on a directory using command line arguments
"""

import argparse
import logging

from uvotredux.reduce import unpack_swift_directory


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
        "-s",
        "--src_region_name",
        help="Path to the source region file",
        default="src.reg",
    )
    parser.add_argument(
        "-b",
        "--bkg_region_name",
        help="Path to the background region file",
        default="bkg.reg",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        help="Overwrite existing files",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    unpack_swift_directory(
        args.swift_obs_dir, args.src_region_name, args.bkg_region_name, args.overwrite
    )
