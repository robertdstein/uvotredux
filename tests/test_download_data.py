"""
Module for testing error handling when the Swift API is unavailable
"""

import unittest
from unittest.mock import MagicMock, patch

from uvotredux.download.data import download_data
from uvotredux.exceptions import SwiftAPIError


class TestDownloadDataApiFailure(unittest.TestCase):
    """
    Class for testing download_data behaviour when the Swift API query fails
    """

    @patch("uvotredux.download.data.ObsQuery")
    def test_rejected_status_raises_clear_error(self, mock_obs_query):
        """
        A rejected/failed API status (e.g. a timeout) should raise a clear
        error rather than being silently treated as "no observations found".

        :return: None
        """

        mock_status = MagicMock()
        mock_status.__bool__.return_value = False
        mock_status.status = "Rejected"
        mock_status.errors = ["Job timed out."]

        mock_oq = MagicMock()
        mock_oq.status = mock_status
        mock_oq.__len__.return_value = 0
        mock_obs_query.return_value = mock_oq

        with self.assertRaises(SwiftAPIError) as context:
            download_data(ra=250.0767333333, dec=26.9258638889)

        self.assertIn("Job timed out.", str(context.exception))
        self.assertIn("Rejected", str(context.exception))

    @patch("uvotredux.download.data.ObsQuery")
    def test_accepted_status_with_no_observations_does_not_raise(self, mock_obs_query):
        """
        A genuinely empty (but successful) query should not raise, only log.

        :return: None
        """

        mock_status = MagicMock()
        mock_status.__bool__.return_value = True
        mock_status.status = "Accepted"
        mock_status.errors = []

        mock_oq = MagicMock()
        mock_oq.status = mock_status
        mock_oq.__len__.return_value = 0
        mock_obs_query.return_value = mock_oq

        # Should return quietly, not raise
        download_data(ra=250.0767333333, dec=26.9258638889)


if __name__ == "__main__":
    unittest.main()
