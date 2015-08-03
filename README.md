# 4U1543
IR data for 4U1543

These programs are hardcoded to work with the directory structure I set up when I was working on 4U1543. However, it is a starting point to making a pipeline to deal with IR data. 

There are three different python programs in this repository: fileLisitng.py, irproc.py, and irphot.py. Each deals with a different part of the IR reduction.

## fileLisitng.py

One of the challanges to dealing with the IR data is that there are many more frames taken at different dither positions for any given observation. A second challenge is that the data are not flatted with IR domes. 

Before we do anything to the data, we will partly address these two problmes by doing some housekeeping and organizing. This will help greatly in the long run.

We will first organize the domes and raw data taken in different dither positions into datastructures. As we reduce the data in later steps, we can use pointers to refer to these datastructures for files and flats that we are interested in.

1. find the raw ir data in the J and H bands (data of the format binirYYMMDD.xxxx.fits) and copy it into subdirectories Jraw/ or Hraw/
2. find the irflats you will need to flatten the data nd copy them into the subdirectory irflats/
3. to create data structures that keep track of the paths, observation dates, and file names of the J and H ir data and J and H domes use filelist.py in your command line.
```shell
python fileListing.py 'J' 'raw' #creates JrawList.pkl
python fileListing.py 'H' 'raw' #creates HrawList.pkl
python fileListing.py 'J' 'flat' #creates JflatList.pkl
python fileListing.py 'H' 'flat' #creates HflatList.pkl
```

Below you will see a screenshot for a typical command sequence to read in these files once you have created them. The screenshot also useses the .head(5) method on the dataframes to show the first 5 lines in the dataframes, to give you a sense of the information they contain. For every file, hey list the observation dates in YYMMDD, the observation date in Julian Date, and the path to the files. This will help us efficently and neatly reference images we are interested in later on in the reduciton.

![first 5 lines of HrawList.pkl and JflatList.pkl](https://github.com/ih64/4U1543/blob/master/tutorial_images/flatpkl_and_filespkl.png)

