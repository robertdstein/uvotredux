"""
Created by Brad Cenko

Updated by Robert Stein on 2024-03-08 to use python3, pathlib, f-strings and gzip
"""

import gzip
import logging
import subprocess
from pathlib import Path

from uvotredux.uvot.filters import filter_dict

logger = logging.getLogger(__name__)


def execute_command(
    cmd: str,
    output_path: Path,
    overwrite: bool = False,
):
    """
    Function to execute a command and handle the output

    :param cmd: Command to execute
    :param output_path: Output path for the command
    :param overwrite: Bool to overwrite existing files
    :return: None
    """
    if output_path.is_file() and overwrite:
        logger.info(f"Removing existing UVOT file: {output_path}")
        output_path.unlink()

    if output_path.is_file():
        logger.info(f"UVOT file already exists: {output_path}")
    else:
        logger.info(f"Executing command: '{cmd}'")
        subprocess.run(cmd, shell=True, check=True)
        logger.info(f"UVOT file created at: {output_path}")

    if not output_path.is_file():
        logger.error(f"UVOT file not created: {output_path}")
        logger.error(f"Command: {cmd}")


def unpack_uvot_images(
    uvot_dir: Path,
) -> list[Path]:
    """
    Function to unpack the swift UVOT images

    :param uvot_dir: Path to the UVOT directory
    :return: List of unpacked images
    """
    swift_images = [x for x in uvot_dir.glob("*_sk.img") if x.is_file()]
    swift_compressed_images = [x for x in uvot_dir.glob("*_sk.img.gz") if x.is_file()]

    logger.info(f"Unpacking Swift observation: {uvot_dir.parent.parent}")
    logger.info(f"Found {len(swift_compressed_images)} compressed images")

    # Uncompress the images
    for image in swift_compressed_images:
        uncompressed_image = image.with_suffix("")
        if not uncompressed_image.is_file():
            logger.info(f"Uncompressing image: {image}")
            with gzip.open(image, "rb") as f_in:
                with open(uncompressed_image, "wb") as f_out:
                    f_out.write(f_in.read())
            swift_images.append(uncompressed_image)

    return swift_images


def unpack_single_uvot_obs(
    swift_obs_dir: Path,
    src_region_path: Path,
    bkg_region_path: Path,
    overwrite: bool = False,
):
    """
    Function to unpack the swift UVOT observation and create the uvot images

    :param swift_obs_dir: Single swift observation directory
    :param src_region_path: Path to the source region file
    :param bkg_region_path: Path to the background region file
    :param overwrite: Overwrite existing files
    :return: None
    """
    uvot_dir = swift_obs_dir / "uvot/image"

    swift_images = unpack_uvot_images(uvot_dir)

    logger.info(f"Found {len(swift_images)} images")

    for image in swift_images:
        uvot_filter = filter_dict[image.name[14:16]]
        uvot_save_path = uvot_dir / f"{uvot_filter}.fits"

        try:
            execute_command(
                cmd=f"uvotimsum {image} {uvot_save_path}",
                output_path=uvot_save_path,
                overwrite=overwrite,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating UVOT image: {e}")
            continue

        if not uvot_save_path.is_file():
            continue

        output_path = uvot_dir / f"{uvot_filter}.out"

        cmd = (
            f"uvotsource image={uvot_save_path} srcreg={src_region_path} "
            f"bkgreg={bkg_region_path} sigma=3.0 outfile={output_path} "
            f"syserr=yes output=ALL apercorr=CURVEOFGROWTH "
            f"> {output_path.with_suffix('.log')}"
        )
        try:
            execute_command(cmd, output_path, overwrite=overwrite)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating UVOT source data: {e}")
            continue
