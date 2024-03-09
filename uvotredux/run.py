"""
Wrapper script to run the swift reduction on a directory using command line arguments
"""

import argparse
import logging

from uvotredux.reduce import unpack_swift_directory

logging.basicConfig(level=logging.INFO)


def main():
    """
    Function to run the swift reduction on a directory

    :return: None
    """
    parser = argparse.ArgumentParser(description="Unpack a Swift UVOT observation")
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
    args = parser.parse_args()
    unpack_swift_directory(
        args.swift_obs_dir, args.src_region_path, args.bkg_region_path
    )
