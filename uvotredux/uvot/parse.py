"""
Module to parse the UVOT results
"""

import logging
from pathlib import Path

import pandas as pd
from astropy.io import fits
from astropy.table import Table

from uvotredux.utils import (
    convert_met_to_utc,
    convert_to_skyportal,
    get_observation_dirs,
)

logger = logging.getLogger(__name__)


def parse_single_uvot_results(
    log_file: Path,
):
    """
    Function to parse the UVOT results from a single observation

    :param log_file: Path to the UVOT log file
    :return: None
    """
    logger.info(f"Parsing UVOT results from: {log_file}")

    with fits.open(log_file) as hdul:
        res = Table(hdul[1].data).to_pandas()  # pylint: disable=no-member

    time = convert_met_to_utc(float(res["MET"][0]))
    res["JD"] = time.jd
    res["ISOT"] = time.isot
    res["MJD"] = time.mjd
    return res


def combine_uvot_results(
    image_output_files: list[Path],
) -> pd.DataFrame:
    """
    Combine the UVOT results from multiple observations

    :param image_output_files: List of UVOT output files
    :return: DataFrame with the combined results
    """
    # Parse each individual UVOT image
    all_df = []
    for uvot_image in sorted(image_output_files):
        parent_dir = uvot_image.parents[2].name
        df = parse_single_uvot_results(uvot_image)
        df["PARENT_DIR"] = parent_dir
        all_df.append(df)

    new_df = pd.concat(all_df)
    new_df.sort_values(by="JD", inplace=True, ignore_index=True)
    return new_df


def parse_uvot_results(
    directory: Path | None = None,
    skyportal: bool = False,
):
    """
    Function to parse the UVOT results from a directory

    :param directory: Directory containing the UVOT observations
    :param skyportal: Convert the results to SkyPortal format
    :return: None
    """

    if directory is None:
        directory = Path.cwd()

    directory = Path(directory)

    logger.info(f"Parsing UVOT results in directory: {directory}")

    # Iterate over directories per visit

    all_uvot_obs = get_observation_dirs(directory)

    # Iterate over each UVOT image in each visit

    all_uvot_images = []

    for obs in all_uvot_obs:
        obs_dir = obs / "uvot/image"
        if not obs_dir.is_dir():
            logger.warning(f"UVOT image directory not found: {obs_dir}")
        all_uvot_images += list(obs_dir.glob("*.out"))

    if len(all_uvot_images) == 0:
        raise FileNotFoundError(f"No UVOT images found in directory: {directory}")

    new_df = combine_uvot_results(all_uvot_images)

    logger.info(f"Found {len(new_df)} UVOT results")

    output_path = directory / "uvot_results.csv"
    new_df.to_csv(output_path)

    slim_df = new_df[
        [
            "ISOT",
            "MJD",
            "RA",
            "DEC",
            "FILTER",
            "EXPOSURE",
            "AB_MAG",
            "AB_MAG_ERR",
            "AB_MAG_LIM",
            "PARENT_DIR",
        ]
    ]
    slim_output_path = directory / "uvot_summary.csv"
    slim_df.to_csv(slim_output_path)
    print(slim_df)

    if skyportal:
        convert_to_skyportal(new_df)
