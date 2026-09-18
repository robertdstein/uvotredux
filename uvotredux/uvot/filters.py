"""
UVOT filters
"""

from pathlib import Path

filter_dict = {
    "vv": "V",
    "bb": "B",
    "uu": "U",
    "w1": "UW1",
    "m2": "UM2",
    "w2": "UW2",
    "wh": "W",
}


def get_uvot_filter(image_path: Path) -> str | None:
    """
    Function to get the UVOT filter name for a raw sk.img image

    :param image_path: Path to the raw sk.img image
    :return: Filter name, or None if the image is not a recognised
        imaging filter (e.g. a grism exposure, which has no entry in
        filter_dict)
    """
    return filter_dict.get(image_path.name[14:16])
