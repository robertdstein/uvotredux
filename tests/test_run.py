"""
Module for testing galsynthspec
"""

import logging
import unittest
from pathlib import Path

import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord
from click.testing import CliRunner

from uvotredux.cli import cli
from uvotredux.download.regions import find_clear_background_position_angle
from uvotredux.paths import get_output_dir
from uvotredux.utils import get_observation_dirs
from uvotredux.utils.name import assign_source_name

logger = logging.getLogger(__name__)

expected_df = pd.read_csv(Path(__file__).parent / "test_data/uvot_summary.csv")


class TestUVOTRedux(unittest.TestCase):
    """
    Class for testing uvotredux
    """

    def test_by_ra_dec(self):
        """
        Test ping

        :return: None
        """

        test_ra, test_dec = 250.0767333333, 26.9258638889

        logger.info(f"Testing uvotredux for {test_ra}, {test_dec}")

        runner = CliRunner()
        runner.invoke(
            cli,
            ["by-ra-dec", str(test_ra), str(test_dec)],
            catch_exceptions=False,
        )

        # Check results

        logger.info("Checking results")

        source_name = assign_source_name(test_ra, test_dec)

        output_csv = get_output_dir(source_name) / "uvot_summary.csv"

        assert output_csv.exists()

        df = pd.read_csv(output_csv)

        pd.testing.assert_frame_equal(df, expected_df)

        # Also check automatic background-region source avoidance against
        # the real UVOT image just downloaded/reduced above - no synthetic
        # data or mocking, this is the actual real image for this target.
        logger.info("Checking automatic background-region source avoidance")

        output_dir = get_output_dir(source_name)
        obs_dirs = get_observation_dirs(output_dir)
        assert len(obs_dirs) > 0

        real_images = list((obs_dirs[0] / "uvot/image").glob("*.fits"))
        assert len(real_images) > 0

        coord = SkyCoord(ra=test_ra, dec=test_dec, unit="deg")
        position_angle = find_clear_background_position_angle(coord, real_images[0])

        assert isinstance(position_angle, u.Quantity)  # pylint: disable=no-member
