import glob
import numpy as np 
from pyraf import iraf
import pandas as pd 
iraf.prcacheOff()

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
	#use iraf imcombine to create the median skyflat
	#','.join(images) concatanates all the images together with a comma between them
	#if we feed it as one string to iraf, it will be recognized as a list of files
	#the produced skyflat will be YYMMDDsky.fits in the current working directory
	iraf.imcombine(','.join(images), date+'sky', headers="", bpmasks="", rejmasks="",
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
	images=dfView.file.values.tolist()
	skySubImages=['sky'+i[5:] for i in images]
	date=str(dfView.Date.values[0])
	iraf.imarith (','.join(images), "-", date+'sky.fits', ','.join(skySubImages), title="sky-subtracted",
		divzero=0., hparams="", pixtype="", calctype="", verbose="yes", noact="no")
	return

def nearestFlat(dfView,color):
	'''
	given the dfview, find the median observation time, and using this time
	identify the jflat that was observed closest in time
	return a string that gives the path to this flat
	'''
	#find the median observation time
	medTime=dfView.JulianDate.median()
	#load up the flat df
	flatDF=pd.read_pickle(color.upper()+'flatList.pkl')
	#subtract the median time form all the flat times, take absolute value, 
	#find index of min, use this index to grab the file name with this observation date
	return flatDF.file[np.argmin(np.abs(flatDF.JulianDate.values - medTime))]

def flatten(flatFile):
	'''grab any sky-subtracted images, and flatten them using flatFile'''
	#first we have to clean up the flat, and get rid of any negative numbers or zeros
	#just set them equal to 1 (???)
	iraf.imreplace(flatFile, 1., imaginary=0., lower="INDEF", upper=1.0, radius=0.)
	#get a list of the sky subtracted images
	skyims=glob.glob('skybinir*fits')
	outputIms=['sky-flatten-'+i[3:] for i in skyims]
	#now flatfield the sky subtracted images
	iraf.ccdproc (','.join(skyims), output=','.join(outimage), 
		ccdtype="", max_cache=0, noproc="no", fixpix="no", overscan="no",
		trim="no", zerocor="no", darkcor="no", flatcor="yes", illumcor="no", fringecor="no",
		readcor="no", scancor="no", readaxis="line", fixfile="", biassec="", trimsec="",
		zero="", dark="", flat=flatFile, illum="", fringe="", minreplace=1.,
		scantype="shortscan", nscan=1, interactive="no", function="legendre", order=1,
		sample="*", naverage=1, niterate=1, low_reject=3., high_reject=3., grow=0.)
	return

