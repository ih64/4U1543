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

def alignReduced(color):
	'''align the flatten images'''
	#grab the paths to the sky subtracted and flattened images
	images_to_align =sorted(glob.glob("reduced/*"+color+"*.fits"))
	#pick the first image in this view as the reference image
	if color=='J':
		ref_image='reduced/140120.J.4U1543.s-f-a-c.fits'
	elif color=='H':
		ref_image='reduced/140120.H.4U1543.s-f-a-c.fits'

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

	for id in identifications:
		if id.ok == True:
			# Variant 2, using geomap/gregister, correcting also for distortions :
			alipy.align.irafalign(id.ukn.filepath, id.uknmatchstars, id.refmatchstars,verbose=False,
				shape=outputshape, makepng=False, outdir="./reduced/"+color+"align/")
	return
