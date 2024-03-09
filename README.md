# uvotredux

`uvotredux` is a simple python wrapper around `HEASoft`, 
which can iteratively reduce Swift UVOT data. 
The actual data reduction is done by `HEASoft`, 
and all credit should go to the NASA team for developing these tools.

## Getting Swift Data

First check if your target has been observed: 
https://www.swift.psu.edu/operations/obsSchedule.php
You should see each visit listed.

You might also see “SSA observations”, but no data is actually taken for those. 
You should just ignore them.

### Downloading Recent Data
For very recent data (from ~2 hours to ~1 month), 
you can download from the quicklook archive: https://swift.gsfc.nasa.gov/cgi-bin/sdc/ql?

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

At this point, you are ready to reduce data!

## Installing HEASoft

To actually reduce Swift data you require NASA's `HEASoft`.

### Installation via Docker
I found installing via Docker to be the easiest. You can find instructions here: 
https://heasarc.gsfc.nasa.gov/lheasoft/docker.html 

You will need to install Docker, and make the `HEASoft` Docker image, following the guide.

Then, start a terminal e.g with:

```bash
docker run -it -rm -v /path/to/swift_data_sn2023uqf:/mydata heasoft:v6.33 bash
```

or whatever version of `HEASoft` you want to use.

This will mount `/path/to/swift_data_sn2023uqf` in the container to `/mydata`, 
so you can reduce the data in that folder.

Then inside the docker container:

```bash
export PATH="/home/heasoft/.local/bin:$PATH"
pip install uvotsource
cd /mydata 
```

### Installation locally
You can instead install `HEASoft` locally, following the official guide: https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/ . In that case, when you are done, run:

```bash
pip install uvotsource
```

And then navigate to the directory containing your data.

## Using uvotredux

Once you are in the data directory you created earlier 
(either in the docker container or the local container if you installed locally), 
you can actually reduce the data.

You can just run the reduction:

```bash
uvotredux
```
This will iteratively reduce each image in the subfolders, 
and that is where you can find reduced images and source tables.

**Make sure you have a fast internet connection, 
because the uvot pipeline can attempt to download fits files >150Mb 
and downloads will time out eventually!**

You can see additional options with:

```bash
uvotredux -h
```
