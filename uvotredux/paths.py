"""
Module for defining paths in the uvotredux application.
"""

import os
from pathlib import Path

default_base_dir = Path(os.getenv("UVOTREDUX_DATA_DIR", Path.home() / "uvotredux_data"))


def get_output_dir(name: str, base_data_dir: Path | str | None = None) -> Path:
    """
    Get the output directory for a given name.

    :param name: Name of the object
    :param base_data_dir: Base directory for data, defaults to default_base_dir
    :return: Path to the output directory
    """
    if base_data_dir is None:
        base_data_dir = default_base_dir
    output_dir = Path(base_data_dir) / name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
