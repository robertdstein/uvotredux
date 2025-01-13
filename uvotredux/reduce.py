"""
Created by Brad Cenko

Updated by Robert Stein on 2024-03-08 to use python3, pathlib, f-strings and gzip
"""

import gzip
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

filter_dict = {
    "vv": "V",
    "bb": "B",
    "uu": "U",
    "w1": "UW1",
    "m2": "UM2",
    "w2": "UW2",
    "wh": "W",
}


def unpack_swift_obs(
    swift_obs_dir: Path,
    src_region_path: Path,
    bkg_region_path: Path,
):
    """
    Function to unpack the swift observation and create the uvot images

    :param swift_obs_dir: Single swift observation directory
    :param src_region_path: Path to the source region file
    :param bkg_region_path: Path to the background region file
    :return: None
    """
    uvot_dir = swift_obs_dir / "uvot/image"

    swift_images = [x for x in uvot_dir.glob("*_sk.img") if x.is_file()]
    swift_compressed_images = [x for x in uvot_dir.glob("*_sk.img.gz") if x.is_file()]

    for image in swift_compressed_images:
        uncompressed_image = image.with_suffix("")
        if not uncompressed_image.is_file():
            logger.info(f"Uncompressing image: {image}")
            with gzip.open(image, "rb") as f_in:
                with open(uncompressed_image, "wb") as f_out:
                    f_out.write(f_in.read())
            swift_images.append(uncompressed_image)

    for image in swift_images:
        uvot_filter = filter_dict[image.name[14:16]]
        uvot_save_path = uvot_dir / f"{uvot_filter}.fits"
        cmd = f"uvotimsum {image} {uvot_save_path}"
        if uvot_save_path.is_file():
            logger.info(f"UVOT image already exists: {uvot_save_path}")
        else:
            logger.info(f"Executing command: '{cmd}'")
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"UVOT image created at: {uvot_save_path}")

        if not uvot_save_path.is_file():
            logger.error(f"UVOT image not created: {uvot_save_path}")
            logger.error(f"Command: {cmd}")
            raise FileNotFoundError(f"UVOT image not created: {uvot_save_path}")

        output_path = uvot_dir / f"{uvot_filter}.out"

        cmd = (
            f"uvotsource image={uvot_save_path} srcreg={src_region_path} "
            f"bkgreg={bkg_region_path} sigma=3.0 outfile={output_path} "
            f"syserr=yes output=ALL apercorr=CURVEOFGROWTH "
            f"> {output_path.with_suffix('.log')}"
        )

        if output_path.is_file():
            logger.info(f"UVOT source data already exists: {output_path}")
        else:
            logger.info(f"Executing command: '{cmd}'")
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"UVOT source data created at: {output_path}")

        if not output_path.is_file():
            logger.error(f"UVOT source data not created: {output_path}")
            logger.error(f"Command: {cmd}")
            raise FileNotFoundError(f"UVOT source data not created: {output_path}")


def unpack_swift_directory(
    directory: Path | None = None,
    src_region_name: str = "src.reg",
    bkg_region_name: str = "bkg.reg",
):
    """
    Function to unpack all the swift observations in a directory

    :param directory: Directory containing the swift observations
    :param src_region_name: Path to the source region file
    :param bkg_region_name: Path to the background region file
    :return: None
    """

    if directory is None:
        directory = Path.cwd()

    directory = Path(directory)

    logger.info(f"Unpacking Swift observations in directory: {directory}")

    all_swift_obs = [
        x
        for x in directory.glob("*")
        if (x.is_dir())
        & (len(x.name) == 11)
        & (sum(not c.isdigit() for c in x.name) == 0)
    ]

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
        unpack_swift_obs(
            swift_obs,
            src_region_path=src_region_path,
            bkg_region_path=bkg_region_path,
        )
