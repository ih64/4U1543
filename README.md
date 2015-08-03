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

Below you will see a screenshot for a typical command sequence to read in these files once you have created them. The screenshot also useses the .head(5) method on the dataframes to show the first 5 lines in the dataframes, to give you a sense of the information they contain. For every file, they list the observation dates in YYMMDD, the observation date in Julian Date, and the path to the files. This will help us efficently and neatly reference images we are interested in later on in the reduciton.

![first 5 lines of HrawList.pkl and JflatList.pkl](https://github.com/ih64/4U1543/blob/master/tutorial_images/flatpkl_and_filespkl.png)

## irproc.py

This module contains several functions that sky subtract, flatten, align, and combine dither positions. It also contains a master function, sameDate, that identifies dither positions takne on the same night, and passes those files off to the other functions for sky subtraction etc and ultimately produces a combined image, and saves it to disk in the reduced/ directory. Let's see how to use it here.

First, ensure that you have followed the instructions above in fileListing.py to create data structures for the J and H flats and images. We will rely on them in this section.

Once that is sorted out, start up python and read in the H or J filelisting into a variable. Then use it with the sameDate function.

For example, run all the raw J data trhough and process, align, and combine all dither positions taken on the same night
```python
import pandas as pd
Jfiles=pd.read_pickle('JrawList.pkl')
sameDate(Jfiles,'J')
```

Or if you only want to run all the H data taken later than 150715 through and process, align, and combine all dither positions taken on the same night

```python
import pandas as pd
Hfiles=pd.read_pickle('HrawList.pkl')
sameDate(Hfiles[H.Date > 150715],'H')
```
