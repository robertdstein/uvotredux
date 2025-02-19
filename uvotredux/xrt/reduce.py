"""
Module to reduce XRT data
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def unpack_single_xrt_obs(
    swift_obs_dir: Path,
    src_region_path: Path,
    # bkg_region_path: Path,
    # overwrite: bool = False,
):
    """
    Function to unpack the swift XRT observation and create the XRT images

    :param swift_obs_dir: Single swift observation directory
    :param src_region_path: Path to the source region file
    :param bkg_region_path: Path to the background region file
    :param overwrite: Overwrite existing files
    :return: None
    """
    xrt_indir = swift_obs_dir / "xrt/event"

    xrt_outdir = swift_obs_dir.parent / (swift_obs_dir.name + "_xrt")
    xrt_outdir.mkdir(parents=True, exist_ok=True)

    # swift_events = [x for x in xrt_indir.glob("*_uf.evt") if x.is_file()]
    # swift_compressed_events = [
    #   x for x in xrt_indir.glob("*_uf.evt.gz") if x.is_file()
    # ]
    #
    # logger.info(f"Unpacking Swift observation: {swift_obs_dir}")
    #
    # logger.info(f"Found {len(swift_compressed_events)} compressed events")
    #
    # for image in swift_compressed_events:
    #     uncompressed_image = image.with_suffix("")
    #     if not uncompressed_image.is_file():
    #         logger.info(f"Uncompressing image: {image}")
    #         with gzip.open(image, "rb") as f_in:
    #             with open(uncompressed_image, "wb") as f_out:
    #                 f_out.write(f_in.read())
    #         swift_events.append(uncompressed_image)
    #
    # logger.info(f"Found {len(swift_events)} events")

    with open(src_region_path, "r", encoding="utf8") as f:
        src_region = f.read()
        ra, dec, _ = src_region.split("(")[1].split(",")
        ra = ra.replace(":", " ")
        dec = dec.replace(":", " ")

    # for event in swift_events:
    #     print(event)
    #
    cmd = (
        f"xrtpipeline indir={swift_obs_dir} outdir={xrt_outdir} "
        f"steminputs={swift_obs_dir.name} "
        f"stemoutputs={swift_obs_dir.name} clobber=yes srcra='{ra}' "
        f"srcdec='{dec}' > {xrt_indir / 'xrtpipeline.log'} "
    )

    print(cmd)
