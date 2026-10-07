"""
Module for testing unpacking of .img.gz files, including mislabelled ones
"""

import gzip
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from astropy.io import fits

from uvotredux.uvot.reduce import unpack_uvot_images

IMAGE_NAME = "sw00012012119uw2_sk.img"


class TestUnpackUvotImages(unittest.TestCase):
    """
    Class for testing unpack_uvot_images
    """

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.tmp_dir.cleanup)
        self.uvot_dir = Path(self.tmp_dir.name)
        self.fits_path = self.uvot_dir / "source.fits"
        fits.PrimaryHDU(np.arange(16, dtype=float).reshape(4, 4)).writeto(
            self.fits_path
        )
        self.gz_path = self.uvot_dir / f"{IMAGE_NAME}.gz"

    def test_gzipped_image_is_uncompressed(self):
        """
        :return: None
        """
        with open(self.fits_path, "rb") as f_in:
            with gzip.open(self.gz_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        images = unpack_uvot_images(self.uvot_dir)

        self.assertEqual(images, [self.uvot_dir / IMAGE_NAME])
        self.assertEqual(images[0].read_bytes(), self.fits_path.read_bytes())

    def test_uncompressed_file_named_gz_is_accepted(self):
        """
        Some downloaded sk.img.gz files are already uncompressed FITS
        (gzip.BadGzipFile: Not a gzipped file (b'SI')) - they should be
        used as they are, not crash the reduction.

        :return: None
        """
        shutil.copyfile(self.fits_path, self.gz_path)

        with self.assertLogs("uvotredux.uvot.reduce", level="WARNING"):
            images = unpack_uvot_images(self.uvot_dir)

        self.assertEqual(images, [self.uvot_dir / IMAGE_NAME])
        self.assertEqual(images[0].read_bytes(), self.fits_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
