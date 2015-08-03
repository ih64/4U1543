import glob, sys, os
import numpy as np 
from pyraf import iraf
import pandas as pd
#append the python path so it can use alipy and stuff
sys.path.append('/home/ih64/python_modules/')
import alipy
#do this stuff down here so IRAF doesn't save any parameters, and to make important tasks avaliable 
iraf.prcacheOff()
iraf.imred()
iraf.ccdred()

def sameDate(df,color):
	'''
	Find the dithers taken on the same night in a filter, sky subtract, flatten, align, combine them
	This function calls all the other functions written below.
	This relies on the files JrawList.pkl, HrawList.pkl, JflatList.pkl, and HflatList.pkl being up to date. For information on how to create
	these files and what they are, look at the documentation in fileListing.py
	INPUT:
	df: a pandas dataframe. read in either JrawList.pkl or HrawList.pkl  to a dataframe 
		to pass to this function, depending which filter you want to redcue
	color: "J", or "H". The filter which data you want to reduce
	OUTPUT:
	for every date being processed, a fits file in the reduced/ subdirectory with the format
	YYMMDD.J.4U1543.s-f-a-c.fits or YYMMDD.J.4U1543.s-f-a-c.fits is written, depending on the value of 'color'

	EXAMPLE:
	#run all the raw J data trhough and process, align, and combine all dither positions taken on the same night
	import pandas as pd
	Jfiles=pd.read_pickle('JrawList.pkl')
	sameDate(Jfiles,'J')
	=================================
	#run all the H data taken later than 150715 through and process, align, and combine all dither positions taken on the same night
	import pandas as pd
	Hfiles=pd.read_pickle('HrawList.pkl')
	sameDate(Hfiles[H.Date > 150715],'H')
	'''
	#measure the number of rows in the dataframe
	size=len(df)
	#initialize two pointers, i and j, which will walk along the dataframe
	#j is ahead of i. we will use them to find files observed on the same night
	#recall that the dataframe is sorted according to observation date
	i=0
	j=i+1
	#while the j pointer is still running through the dataframe ...
	while j < size:
		#look at the date at the position of i and j
		dateI=df.Date.iloc[i]
		dateJ=df.Date.iloc[j]
		#if the dates are equal, move j forward one step
		if dateI==dateJ:
			j+=1
		#otherwise, return the section of the dataframe between the
		#i and j pointesr. this part of the dataframe has images taken from the same night
		#we can pass them on to other functions to do sky subtraction, flattening, aligning, and combining
		else:
			dfView = df.iloc[i:j]
			makeSkyFlat(dfView)
			skySub(dfView)
			flatFile=nearestFlat(dfView,color)
			flatten(flatFile)
			#the exitFlag will equal True if align() was able to align 2 or more dithers
			#if the exitFlag is true, then combine the aligned dither positions
			exitFlag=align()
			if exitFlag:
				combineDithers(color)
			#otherwise, just pass over these dither positions
			else:
				print "we could not successfully align 2 or more dither positions"
				print "there will not combined image for this dither set"
			#remove the intermediary files that were saved in scratch/
			cleanup('scratch/')
			#move i up to j's current position
			i=j
			#move j up one
			j+=1
	#we have fallen out of the loop. This means that the entries between the i and the end of the df
	#all belong to the most recent observation date. lets reduce those too.
	dfView = df.iloc[i:j]
	makeSkyFlat(dfView)
	skySub(dfView)
	flatFile=nearestFlat(dfView,color)
	flatten(flatFile)
	exitFlag=align()
	if exitFlag:
		combineDithers(color)
	else:
		print "we could not successfully align 2 or more dither positions"
		print "there will not combined image for this dither set"
	#remove the intermediary files that were saved in scratch/
	cleanup('scratch/')
	return



def joinStrList(fileList, scratch=False):
	'''
	given a list that has paths to data,
	join the file paths in a long string
	where each element is seperated by a comma.
	this long string can then be passed as an image list 
	to python tasks
	if scratch is set to True, concatinate the string 'scratch/'
	to each element before joining them. the scratch directory
	is where we will put temporary output fits files for the reduction
	'''
	if scratch==True:
		longString=','.join(['scratch/'+i for i in fileList])
		return longString
	elif scratch==False:
		longString=','.join(fileList)
		return longString
	else:
		print 'set scratch equal to either True or False'
		return

def makeSkyFlat(dfView):
	'''
	dfView is a view from either the {J,H}rawFileList data frame
	the view should contain dither positions of the same observation
	this module will calculate the skyflat from the dither positions
	and save it
	'''
	#gather up the images in a python list
	images=dfView.file.values.tolist()
	#they should all have the same date, just grab the first one
	date=str(dfView.Date.values[0])
	#organize the images and output file name in iraf-friendly ways
	inputFiles=joinStrList(images)
	outputSkyFlat='scratch/'+date+'sky'
	#use iraf imcombine to create the median skyflat
	iraf.imcombine(inputFiles, outputSkyFlat, headers="", bpmasks="", rejmasks="",
		nrejmasks="", expmasks="", sigmas="", imcmb="$I", logfile="STDOUT", combine="median", 
		reject="none", project="no", outtype="real", outlimits="", offsets="none", masktype="none",
		maskvalue="0", blank=0., scale="none", zero="none", weight="none", statsec="",
		expname="", lthreshold="INDEF", hthreshold="INDEF", nlow=1, nhigh=2, nkeep=1,
		mclip="yes", lsigma=3., hsigma=3., rdnoise="0.", gain="1.", snoise="0.",
		sigscale=0.1, pclip=-0.5, grow=0.)
	return

def skySub(dfView):
	'''
	given the dfview, and using the skyflat calculated in makeSkyFlat,
	subtract the skyflat from each image
	the output will be one sky-subtracted image for each image in the dfView
	the names of the sky-subtracted fits images have 'sky' infront of them
	'''
	#grab the paths to images to be sky-subtracted
	images=dfView.file.values.tolist()
	#adding a 's' infront of each file name, save to a seperate list
	skySubImages=['s-'+i[5:] for i in images]
	#grab the YYMMDD observation date from this view
	date=str(dfView.Date.values[0])

	#organize the input, skyflat, and output in iraf-friendly ways
	inputFiles=joinStrList(images)
	skyFlat='scratch/'+date+'sky.fits'
	outputSkySub=joinStrList(skySubImages, scratch=True)
	iraf.imarith (inputFiles, "-", skyFlat, outputSkySub, 
		divzero=0., hparams="", pixtype="", calctype="", verbose="yes", noact="no")
	return

def nearestFlat(dfView,color):
	'''
	given the dfview, find the median observation time, and using this time
	identify the jflat that was observed closest in time
	return a string that gives the path to this flat
	'''
	#find the median observation time of the dfView
	medTime=dfView.JulianDate.median()
	#load up the flat df
	flatDF=pd.read_pickle(color.upper()+'flatList.pkl')
	#subtract the median time form all the flat times, take absolute value, 
	#find index of min, use this index to grab the file name with this observation date
	return flatDF.file[np.argmin(np.abs(flatDF.JulianDate.values - medTime))]

def flatten(flatFile):
	'''grab any sky-subtracted images, and flatten them using flatFile'''
	#first we have to clean up the flat, and get rid of any negative numbers or zeros
	#just set them equal to 1 (??? why do we do this ???)
	iraf.imreplace(flatFile, 1., imaginary=0., lower="INDEF", upper=1.0, radius=0.)
	#get a list of the sky subtracted images
	skyims=glob.glob('scratch/s-binir*fits')
	flatIms=['s-f-'+i[10:] for i in skyims]
	#organize input and output in iraf-friendly ways
	inputFiles=joinStrList(skyims)
	outputFiles=joinStrList(flatIms, scratch=True)
	#now flatfield the sky subtracted images
	iraf.ccdproc(images=inputFiles, output=outputFiles, 
		ccdtype="", max_cache=0, noproc="no", fixpix="no", overscan="no",
		trim="no", zerocor="no", darkcor="no", flatcor="yes", illumcor="no", fringecor="no",
		readcor="no", scancor="no", readaxis="line", fixfile="", biassec="", trimsec="",
		zero="", dark="", flat=flatFile, illum="", fringe="", minreplace=1.,
		scantype="shortscan", nscan=1, interactive="no", function="legendre", order=1,
		sample="*", naverage=1, niterate=1, low_reject=3., high_reject=3., grow=0.)
	return

def align():
	'''align the flatten images'''
	#grab the paths to the sky subtracted and flattened images
	images_to_align =sorted(glob.glob("scratch/s-f-*fits"))
	#pick the first image in this view as the reference image
	ref_image = images_to_align[0]

	#everything below here i copied from the alipy demo http://obswww.unige.ch/~tewes/alipy/tutorial.html
	identifications = alipy.ident.run(ref_image, images_to_align, visu=False)
	# That's it !
	# Put visu=True to get visualizations in form of png files (nice but much slower)
	# On multi-extension data, you will want to specify the hdu (see API doc).

	# The output is a list of Identification objects, which contain the transforms :
	for id in identifications: # list of the same length as images_to_align.
		if id.ok == True: # i.e., if it worked
			print "%20s : %20s, flux ratio %.2f" % (id.ukn.name, id.trans, id.medfluxratio)
			# id.trans is a alipy.star.SimpleTransform object. Instead of printing it out as a string,
			# you can directly access its parameters :
			#print id.trans.v # the raw data, [r*cos(theta)  r*sin(theta)  r*shift_x  r*shift_y]
			#print id.trans.matrixform()
			#print id.trans.inverse() # this returns a new SimpleTransform object
		else:
			print "%20s : no transformation found !" % (id.ukn.name)

	# Minimal example of how to align images :
	outputshape = alipy.align.shape(ref_image)
	# This is simply a tuple (width, height)... you could specify any other shape.

	#initialize numGoodAlign, it will keep tally of the dither positions we were able to align
	numGoodAlign=0

	for id in identifications:
		if id.ok == True:
			# Variant 2, using geomap/gregister, correcting also for distortions :
			alipy.align.irafalign(id.ukn.filepath, id.uknmatchstars, id.refmatchstars,verbose=False,
				shape=outputshape, makepng=False, outdir="./scratch")

			#if we were able to align this dither frame, incrament numGoodAlign by one
			numGoodAlign+=1

	#if we could align at least two frames successfully, then return True
	if numGoodAlign >= 2:
		return True
	else:
		return False

def combineDithers(color):
	'''grab the aligned images and sum them up into one'''
	#grab the paths to the sky subtracted flattened aligned images
	aligned=sorted(glob.glob('scratch/s-f-*_gregister.fits'))
	#pick out the YYMMDD date from the file names
	date=aligned[0][17:23]

	#organize input and output in iraf-friendly ways
	inputFiles=joinStrList(aligned)
	outputFile='reduced/'+date+'.'+color+'.4U1543.s-f-a-c'
	#use iraf imcombine to sum them all up
	iraf.imcombine(inputFiles, outputFile,
		headers="", bpmasks="", rejmasks="", nrejmasks="", expmasks="",
		sigmas="", imcmb="$I", logfile="STDOUT", combine="sum", reject="none",
		project="no", outtype="real", outlimits="", offsets="none", masktype="none",
		maskvalue="0", blank=0., scale="none", zero="none", weight="none", statsec="",
		expname="", lthreshold="INDEF", hthreshold="INDEF", nlow=1, nhigh=2, nkeep=1,
		mclip="yes", lsigma=3., hsigma=3., rdnoise="0.", gain="1.", snoise="0.",
		sigscale=0.1, pclip=-0.5, grow=0.)
	return

def cleanup(path):
	'''delete everything under the path directory'''
	scratchFiles=glob.glob(path+'*')
	for f in scratchFiles:
		os.remove(f)
	#os.remove('/home/ih64/Desktop/4U1543/logfile')
	return
