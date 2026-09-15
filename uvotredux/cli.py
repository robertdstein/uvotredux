"""
CLI tools for uvotredux
"""

import logging

import click

from uvotredux.paths import get_output_dir
from uvotredux.run import main
from uvotredux.utils.name import assign_source_name
from uvotredux.utils.tns import get_tns_by_name

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


def shared_options(func):
    """
    Decorator to add shared options to CLI commands.

    :param func: Function to decorate
    :return: Decorated function with shared options
    """
    func = click.option(
        "--download/--skip-download", default=True, help="Enable using cached results"
    )(func)
    func = click.option(
        "-d",
        "--swift_obs_dir",
        default=None,
        help="Path to the base Swift observation directory",
    )(func)
    func = click.option(
        "-o",
        "--overwrite",
        is_flag=True,
        help="Overwrite existing files",
        default=False,
    )(func)
    return func


@click.group()
def cli():
    """
    CLI for uvotredux
    """


@cli.command("by-name")
@click.argument("name", type=str)
@shared_options
def run_by_name(name: str, download: bool, swift_obs_dir: str | None, overwrite: bool):
    """
    Run uvotredux by name.
    """
    logger.info(f"Running pipeline for source name {name}")

    output_dir = get_output_dir(name, base_data_dir=swift_obs_dir)

    tns_data = get_tns_by_name(name, output_dir=output_dir)
    if tns_data is None:
        logger.error(
            f"Could not find TNS data for {name}. "
            f"Please check the name and try again."
        )
        return
    main(
        ra_deg=tns_data["ra"],
        dec_deg=tns_data["dec"],
        output_dir=output_dir,
        overwrite=overwrite,
        download=download,
    )


@cli.command("by-ra-dec", context_settings={"ignore_unknown_options": True})
@click.argument("ra_deg", type=str)
@click.argument("dec_deg", type=str)
@shared_options
def run_by_ra_dec(
    ra_deg: float | str,
    dec_deg: float | str,
    download: bool,
    swift_obs_dir: str | None,
    overwrite: bool,
):
    """
    Run uvotredux by RA and Dec.

    :param ra_deg: Right Ascension in degrees
    :param dec_deg: Declination in degrees
    :param download: Whether to download the data or not
    :param swift_obs_dir: Base directory for Swift observations
    :param overwrite: Overwrite existing files

    :return: None
    """
    logger.info(f"Running pipeline for position {ra_deg} {dec_deg}")

    name = assign_source_name(ra_deg, dec_deg)

    output_dir = get_output_dir(name, base_data_dir=swift_obs_dir)

    main(
        ra_deg=float(ra_deg),
        dec_deg=float(dec_deg),
        output_dir=output_dir,
        overwrite=overwrite,
        download=download,
    )
