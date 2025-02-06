"""
Utility functions for the UVOT redux package.
"""

from pathlib import Path


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
