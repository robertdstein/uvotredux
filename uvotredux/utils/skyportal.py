"""
Module to format the UVOT results for SkyPortal
"""

import io

import pandas as pd


def convert_to_skyportal(df: pd.DataFrame):
    """
    Function to convert the UVOT results to a SkyPortal-compatible format

    :param df: DataFrame with the UVOT results
    :return: String with the SkyPortal-compatible format
    """

    new = df.copy()

    mapping = {
        "MJD": "mjd",
        "AB_MAG": "mag",
        "AB_MAG_ERR": "magerr",
        "AB_MAG_LIM": "limiting_mag",
    }

    new.rename(columns=mapping, inplace=True)
    new["magsys"] = "ab"
    filters = [f"uvot::{x.lower().strip()}" for x in new["FILTER"]]
    new["filter"] = filters

    mask = new["mag"] < 99.0  # & (new["mag"] < new["limiting_mag"])

    cut = new[mask][list(mapping.values()) + ["magsys", "filter"]]

    mask = cut["mag"] > cut["limiting_mag"]
    cut.loc[mask, "mag"] = None
    cut.loc[mask, "magerr"] = None

    with io.StringIO() as f:
        cut.to_csv(f, index=False)
        print(f.getvalue())
