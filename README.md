# 4U1543
IR data for 4U1543

These programs are hardcoded to work with the directory structure I set up when I was working on 4U1543. However, it is a starting point to making a pipeline to deal with IR data. 

I'll describe the directory structure I had explicitly, so you can either mimic it or make appropriate corrections to the code if you want to clone this directory to your machine.

Everything is under on thuban  
/scratch/xrb-photometry/4U1543  
* fileListing.py  
* irphot.py  
* irproc.py  
* Hraw/  
* Jraw/  
* irflats/  
* reduced/  
   * Halign/  
   * Jalign/  
* scratch/  

copy all the unprocessed binirYYMMDD.xxxx.fits data into either the Hraw or Jraw directory, depending on the filter.

If you set all that up in your end, you should be good to go.

There are three different python programs in this repository: fileLisitng.py, irproc.py, and irphot.py. Each deals with a different part of the IR reduction. I'll discuss each by itself below

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

note that this will take a while to run. this is because the entire *List.pkl files are recreated rather than updated. this is an odvious area for improvement.

## irproc.py

This module contains several functions that sky subtract, flatten, align, and combine dither positions. It also contains a master function, sameDate, that identifies dither positions takne on the same night, and passes those files off to the other functions for sky subtraction etc and ultimately produces a combined image, and saves it to disk in the reduced/ directory. Let's see how to use it here.

First, ensure that you have followed the instructions above in fileListing.py to create data structures for the J and H flats and images. We will rely on them in this section.

Once that is sorted out, start up python and read in the H or J filelisting, and pass it to the sameDate function. The sameDate function accepts two arguments, the first is a pandas dataframe read in from either HrawList.pkl or JrawList.pkl. The second is the filter you are working on, either 'J' or 'H'. The second argument is used to ensure we look up appropriate irflats. 

I'll show you a few examples with some typical command sequences to use after starting up python. 

For example, to run all the raw J data trhough and process, align, and combine all dither positions taken on the same night
```python
import irproc
import pandas as pd
Jfiles=pd.read_pickle('JrawList.pkl')
irproc.sameDate(Jfiles,'J')
```

Or if you only want to run all the H data taken *later than 150715* through and process, align, and combine all dither positions taken on the same night

```python
import irproc
import pandas as pd
Hfiles=pd.read_pickle('HrawList.pkl')
irproc.sameDate(Hfiles[Hfiles.Date > 150715],'H')
```

Or maybe you want to work on J data taken on a very specific date (150715 in the example below)
```python
import irproc
import pandas as pd
Jfiles=pd.read_pickle('JrawList.pkl')
irproc.sameDate(Jfiles[Jfiles.Date == 150715],'J')
```

You will see a lot of output in your terminal. For every set of dither images, the following happens

1. the sky background is calculated by median combining the dither positions
2. the sky is then subtracted from each dither position
3. the flat which was taken closest in time to this observation is found in the the flatList
4. the different dither positions are flattened with the flat found in step 3
5. we attempt to align the different dither positions together
6. dither positions which were successfully aligned are then combined and saved under reduced/. if fewer than 2 dithers were successfuly alligned, we do not attempt to combine the images.
7. the intermediary files which were generated and temporarily saved in the scratch/ directory in the process are removed

If you want to understand in greater detail how this function works, I'd encourage you to open up irproc.py in a text editor and examine the code. I've taken great care to leave docstrings for each function, and comments describing what each function is doing.

## irphot.py

This module contains functions to do apertury photometry on the images created by irproc.py. It is not streamlined yet-there is no master function that calls the others, and using it is a little clunky at the moment. 

### irphot.alignReuced

The first step is to align the new reduced & combined ir images to a common coordinate system. In the directories reduced/Jalign and reduced/Halign the aligned versions of the images under reduced are saved. To align an image, we use the alignReduced method.

For example, in the last code block in the section above we did ir reduction for J data taken on 150715. That created the file reduced/150715.J.4U1543.s-f-a-c.fits. To align this image we would do start up python and do
```python
import irphot
irphot.alignReduced('J',['reduced/150715.J.4U1543.s-f-a-c.fits'])
```

The first argument is the filter the data was taken in. The second argument is a python list containing the paths to the images you want to align. The output will be a new file with the extension '_gregister.fits' for every file in the second argument. For example, the above commands will create the file reduced/Jalign/150715.J.4U1543.s-f-a-c_gregister.fits.

It is also possible to align a bunch of images at once. Just add them to the list in the second argument. For example, 
```python
irphot.alignReduced('H',['reduced/150715.H.J.4U1543.s-f-a-c.fits','reduced/150717.H.4U1543.s-f-a-c.fits'])
```
aligns h data taken on 150715 *and* 150717.

### irphot.photometry

now we can do aperture photometry on the images we created in the previous section. the command sequence is almost identical as the one we used for irphto.alignReduced. We will pass the filter and a list containing the centered images to the photometry method

```python
import irphot
irphot.photometry('J',['reduced/Jalign/150715.J.4U1543.s-f-a-c_gregister.fits'])
```

will do photometry on reduced/Jalign/150715.J.4U1543.s-f-a-c_gregister.fits and create the mag file reduced/Jalign/150715.J.4U1543.s-f-a-c_gregister.fits.MC which contains the output from photometry.

```python
irphot.photometry('H',['reduced/Halign/150715.H.J.4U1543.s-f-a-c_gregister.fits','reduced/Halign/150717.H.4U1543.s-f-a-c_gregister.fits'])
```

will do photometry on the two H images.

### irphot.magtodf

now that we have many output files from photometry, we can gather them all up in a pandas dataframe. The method magtodf will do all the heavy lifting for us, we just need to tell it what filter we care about.

```python
irphot.magtodf('J') #get all the Jband photometry data
irphot.magtodf('H') #get all the Hband photometry data
```

this will create Jphot.pkl and Hphot.pkl, pickeled versions of the dataframes created by the magtodf. see the screenshot below to look at a command sequence to read in the dataframe and see some of the contents. information like observation date, instrumental magnitudes, errors, and the Calibrated magnitude are given. The Calibrated Magnitude bit is hardcoded for 4U1543's comparison stars and their 2MASS magnitudes

![photometry dataframe](https://github.com/ih64/4U1543/blob/master/tutorial_images/photdf.png)

Note that this will take a while to run. This is because the program *recreates the entire dataframe* by looking at each photometry output file rather than simply updating it. As an improvement, you can change this up.

### irphot.lightCurve

for kicks, I threw in a method that will create a light curve of the H and J data. just do `irphot.lightCurve()` and you will get a two panel light curve with the data. the scale may be funny if there are outliers in the data, but it is easy to change the display with the matplotlib GUI.

![lightcuve, after the y ranges were changed](https://github.com/ih64/4U1543/blob/master/tutorial_images/lightcurve.png)
