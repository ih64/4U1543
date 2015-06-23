import numpy as np 
from pyraf import iraf
import pandas as pd 


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
	date=str(dfView.Date[0])
	#use iraf imcombine to create the median skyflat
	#','.join(images) concatanates all the images together with a comma between them
	#if we feed it as one string to iraf, it will be recognized as a list of files
	#the produced skyflat will be datesky.fits in the current working directory
	iraf.imcombine(','.join(images), date+'sky', headers="", bpmasks="", rejmasks="",
		nrejmasks="", expmasks="", sigmas="", imcmb="$I", logfile="STDOUT", combine="median", 
		reject="none", project=no, outtype="real", outlimits="", offsets="none", masktype="none",
		maskvalue="0", blank=0., scale="none", zero="none", weight="none", statsec="",
		expname="", lthreshold=INDEF, hthreshold=INDEF, nlow=1, nhigh=2, nkeep=1,
		mclip=yes, lsigma=3., hsigma=3., rdnoise="0.", gain="1.", snoise="0.",
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
	skySubImages=['sky'+i for i in images]
	date=str(dfView.Date[0])
	imarith (','.join(images), "-", date+'sky.fits' ','.join(skySubImages), title="sky-subtracted",
		divzero=0., hparams="", pixtype="", calctype="", verbose=yes, noact=no)
	return

