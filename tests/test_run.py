"""
Module for testing galsynthspec
"""

import logging
import unittest
from pathlib import Path

import pandas as pd
from click.testing import CliRunner

from uvotredux.cli import cli
from uvotredux.paths import get_output_dir
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
