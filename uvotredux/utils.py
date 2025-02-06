"""
Utility functions for the UVOT redux package.
"""

from pathlib import Path

from astropy.time import Time

# Swift times are in MET, defined as seconds since 2001-01-01T00:00:00
SWIFT_T0 = Time("2001-01-01T00:00:00", scale="tt", format="isot")
SECONDS_IN_DAY = 60.0 * 60.0 * 24.0


def convert_met_to_utc(met: float) -> Time:
    """
    Function to convert mission elapsed time (MET) to UTC time

    :param met: MET time
    :return: UTC time
    """
    return Time(SWIFT_T0.mjd + met / SECONDS_IN_DAY, format="mjd", scale="utc")


def get_observation_dirs(
    parent_directory: Path,
) -> list[Path]:
    """
    Identify the directories in the parent directory
    that are likely Swift observations

    :param parent_directory: Parent directory
    :return: List of directories
    """
    res = [
        x
        for x in parent_directory.glob("*")
        if (x.is_dir())
        & (len(x.name) == 11)
        & (sum(not c.isdigit() for c in x.name) == 0)
    ]
    return res
