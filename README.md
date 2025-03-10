# uvotredux

[![PyPI version](https://badge.fury.io/py/uvotredux.svg)](https://badge.fury.io/py/uvotredux)

`uvotredux` is a simple python wrapper around `HEASoft`, 
which can iteratively reduce Swift UVOT data. 
The actual data reduction is done by `HEASoft`, 
while the downloading is done with `swifttools`.
All credit should go to the Swift team for developing these tools.

You will need to create a parent directory for the swift data. 
uvotredux will then download the actual data using `swifttools`. 

## Installing HEASoft

To actually reduce Swift data you require NASA's `HEASoft`.

### Installation via Docker
I found installing via Docker to be the easiest. You can find instructions here: 
https://heasarc.gsfc.nasa.gov/lheasoft/docker.html 

You will need to install Docker, and make the `HEASoft` Docker image, following the guide.

Then, there are two ways to use uvotredux:

#### Docker with PyPi uvotredux

Then, start a terminal e.g with:

```bash
docker run -it --rm -v /path/to/swift_data_sn2023uqf:/mydata heasoft:v6.33 bash
```

or whatever version of `HEASoft` you want to use.

This will mount `/path/to/swift_data_sn2023uqf` in the container to `/mydata`, 
so you can download and reduce the data in that folder.

Then inside the docker container:

```bash
export PATH="/home/heasoft/.local/bin:$PATH"
pip install -e /uvotredux
cd /mydata 
```

#### Docker with local (editable) uvotredux

If you want to edit the code, you can instead clone the repository somewhere on your machine:

```bash
git clone https://github.com/robertdstein/uvotredux.git
```

Then, start the docker container with:

```bash
docker run -it --rm -v /path/to/swift_data_sn2023uqf:/mydata -v /path/to/uvotredux:/uvotredux heasoft:v6.33 bash
```

Then inside the docker container:

```bash
export PATH="/home/heasoft/.local/bin:$PATH"
cd /uvotredux
pip install -e .
cd /mydata 
```

### Installation locally
You can instead install `HEASoft` locally, following the official guide: https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/ . In that case, when you are done, run:

```bash
pip install uvotredux
```

And then navigate to the directory which either contains your data, or where you want to download the data.

## Using uvotredux

Once you are in the data directory you created earlier 
(either in the docker container or the local directory if you installed locally), 
you can start downloading data.

### Downloading Data

You can download data with:

```bash
uvotdownload --ra 133.457 --dec 25.119
```

or whatever the coordinates of your target are. 
uvotredux will check the Swift archive, and download images.
By default, it will not overwrite existing files, 
but you can change that with `--overwrite`.

In your directory, you should see a subdirectory for each visit.

## Reducing Data

You can then actually reduce the data. In the same directory, you can just run the reduction:

```bash
uvotredux
```
This will iteratively reduce each image in the subfolders, 
and that is where you can find reduced images and source tables.

The code will scrape the output files of each individual image, 
and produce a combined csv file with all the available info (`uvot_results.csv`).
Beware: this file conrtains over a hundred columns per image.

There is also a smaller file (`uvot_summary.csv`) that contains only the most important columns.

**Make sure you have a fast internet connection, 
because the uvot pipeline can attempt to download fits files >150Mb 
and downloads will time out eventually!**

You can see additional options with:

```bash
uvotredux -h
```


## Getting Data Manually

## Getting Swift Data

First check if your target has been observed: 
https://www.swift.psu.edu/operations/obsSchedule.php
You should see each visit listed.

You might also see “SSA observations”, but no data is actually taken for those. 
You should just ignore them.

### Downloading Recent Data
For very recent data (from ~2 hours to ~1 month), 
you can download from the quicklook archive: https://swift.gsfc.nasa.gov/sdc/ql/

You can search for your target, and then download the data.
Make sure you tick the box to include UVOT data!

You will get a tar file for each visit, which you can decompress.
Place each decompressed directory in a parent directory. 
Give the parent directory a name that is informative, e.g `swift_data_sn2023uqf`.


### Downloading Old Data
For old data, check the archive: https://www.swift.ac.uk/swift_portal/
(After you found the archive data, download it as a tar/zip and make sure you tick the box to include UVOT data!)

You will see a file named `download.tar` or `download.zip`. 
I suggest renaming this to something more informative e.g `swift_data_sn2023uqf.zip` 
or `swift_data_sn2023uqf.tar`.

Finally, you should decompress your files. On mac/linux this is easy. 
You will get a directory with the same name as the tar/zip file.

## Setting up Extraction Regions
Whether you downloaded recent or old data, the parent data directory is 
where you can run the iterative data reduction. 
It’ll look like:

`swift_data_sn2023uqf/`
- 00016282001
- 00016282002
- 00016282003
- …

And so on, with one subdirectory for each Swift visit of your target. 
There are compressed images in these subdirectories, 
but uvotredux will be able to unpack them for you automatically later on.

In the directory `swift_data_sn2023uqf/`, 
you need to create two .reg files. One is your source, 
centered at the position with an appropriate radius. 
The other is a background region, and that should be free of other sources!

These files are just plain text files containing a single line, of the form:
```txt
fk5;circle(09:33:49.15,+25:06:56.86,3")
```
and
```txt
fk5;circle(43.45786323544644,25.119753601756596,12")
```

To test the extraction region, I suggest taking the reddest image, 
uncompressing the _sk.img.gz file, and opening it in ds9. 
Then you can overlay the regions to see if they are centered correctly.

At this point, you are ready to reduce data!
