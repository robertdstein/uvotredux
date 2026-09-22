"""
Module for testing make_source_region
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from uvotredux.download.source_region import make_source_region, src_path

TEST_RA, TEST_DEC = 250.0767333333, 26.9258638889


class TestMakeSourceRegion(unittest.TestCase):
    """
    Class for testing make_source_region
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.base_dir = Path(self.tmp_dir.name)

    def test_skips_when_already_exists_and_not_overwrite(self):
        """
        An existing src.reg should be left untouched when overwrite=False.

        :return: None
        """
        src_path(self.base_dir).write_text("fk5;circle(1,1,1)\n", encoding="utf8")

        make_source_region(
            ra=TEST_RA,
            dec=TEST_DEC,
            base_dir=self.base_dir,
            overwrite=False,
        )

        self.assertEqual(
            src_path(self.base_dir).read_text(encoding="utf8"),
            "fk5;circle(1,1,1)\n",
        )

    def test_default_output(self):
        """
        :return: None
        """
        make_source_region(ra=TEST_RA, dec=TEST_DEC, base_dir=self.base_dir)

        content = src_path(self.base_dir).read_text(encoding="utf8")
        self.assertEqual(content, 'fk5;circle(16:40:18.42,26:55:33.11,3")\n')


class TestDefaultBaseDir(unittest.TestCase):
    """
    Class for testing that make_source_region defaults to the current
    working directory when base_dir is not given
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self._original_cwd = Path.cwd()
        os.chdir(self.tmp_dir.name)
        self.addCleanup(os.chdir, self._original_cwd)

    def test_make_source_region_defaults_to_cwd(self):
        """
        :return: None
        """
        make_source_region(ra=TEST_RA, dec=TEST_DEC)
        self.assertTrue(src_path(Path.cwd()).is_file())


if __name__ == "__main__":
    unittest.main()
