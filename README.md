# uvotredux

[![PyPI version](https://badge.fury.io/py/uvotredux.svg)](https://badge.fury.io/py/uvotredux)

`uvotredux` is a simple python wrapper around `HEASoft`, 
which can iteratively reduce Swift UVOT data. 
The actual data reduction is done by `HEASoft`, 
while the downloading is done with `swifttools`.
All credit should go to the Swift team for developing these tools.

I strongly recommend using `uvotredux` in a Docker container.

## Installing and using a stable uvotredux release with Docker

You can pull the latest version of `uvotredux` from Docker Hub:

```bash
docker pull robertdstein/uvotredux:latest
```

You need a working docker installation for this. 
This image contains the latest version of `uvotredux`, and `heasoft`.

Then you can run the container with:

```bash
docker run -it --rm -v ~/path/to/local/data:/mydata robertdstein/uvotredux:latest ARGS
```

where `/path/to/local/data` is the path to the directory where you want to download the data,
and `ARGS` are the arguments you want to pass to `uvotredux`.

### Creating a convenient alias for uvotredux

You can create a convenient alias in your shell configuration file (e.g., `.bashrc` or `.zshrc`) to simplify the command:

```bash
alias uvotredux='docker run --rm -v /path/to/local/data:/mydata robertdstein/uvotredux:latest'
```

Then, to download and reduce data for a target at RA 133.457 and Dec 25.119, you can run:

```bash
uvotredux by-ra-dec 133.457 25.119
```

or to download and reduce data for a target with a specific name, you can run:

```bash
uvotredux by-name AT2025mav
```

## Installing and using a stable uvotredux release using pip with local HEASoft

If you already have heasoft installed locally, you can also install `uvotredux` via pip:

```bash
pip install uvotredux
```

This will install the latest stable release of `uvotredux` from PyPI.

Then you can set the data directory where you want to download/reduce the data:

```bash
export UVOTREDUX_DATA_DIR="/path/to/local/data"
```

and then run `uvotredux` with the desired arguments, e.g.:

```bash
uvotredux by-ra-dec 133.457 25.119
```

## Installing and using uvotredux in an editable state with Docker

If you want to edit the code, you will still need a working docker installation of heasoft:

```bash
docker pull robertdstein/uvotredux:latest
```

Then, you can clone the repository somewhere on your machine:

```bash
git clone https://github.com/robertdstein/uvotredux.git
```

Then, start the docker container with:

```bash
docker run --rm -it --entrypoint bash -v /path/to/local/data:/mydata -v /path/to/local/uvotredux:/uvotredux robertdstein/uvotredux:latest
```

This will mount your local data directory to `/mydata` in the container,
and your local `uvotredux` directory to `/uvotredux` in the container.

Then inside the docker container, you can install `uvotredux` in editable mode:

```bash
export PATH="/home/heasoft/.local/bin:$PATH"
pip install -e /uvotredux
```

And finally, within the docker container, you can run `uvotredux` commands as usual:

```bash
uvotredux by-ra-dec 133.457 25.119
```

## Using uvotredux

Uvotredux will download the data for you, if it is not already present in the specified data directory.

It will then iteratively reduce each image in the subfolders of the data directory.

**Make sure you have a fast internet connection, because the uvot pipeline can attempt to download calibration fits files that are >150Mb and downloads will time out eventually!**

The code will scrape the output files of each individual image, 
and produce a combined csv file with all the available info (`uvot_results.csv`).
Beware: this file contains over a hundred columns per image.

There is also a smaller file (`uvot_summary.csv`) that contains only the most important columns.

### Checking the Results

Imagine you reduced data for a target with the name `AT2025mav`.

You will see a directory created in your local data directory: `/path/to/local/data/AT2025mav` .

In the directory there will be a subdirectory for each visit, as well as a `uvot_results.csv` and `uvot_summary.csv` file.
There are also two region files (`src.reg` and `bkg.reg`) that were used extract the source and background regions.

`uvotredux` generates these automatically. However, it is possible that an unrelated source is present in the background region.
You can check this by opening up one of the uncompressed images in ds9, e.g `/path/to/local/data/AT2025mav/00019808001/uvot/image/UW2.fits`.
You can then overlay the regions from the `src.reg` and `bkg.reg` files to see if they are centered correctly.
