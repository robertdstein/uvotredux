"""
Functions for calculating the MET (Modified Julian Date) of a given date.
"""

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
