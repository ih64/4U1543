import glob, sys, os
import numpy as np 
from pyraf import iraf
from astropy.io import ascii
import pandas as pd
import matplotlib.pyplot as plt
#append the python path so it can use alipy and stuff
sys.path.append('/home/ih64/python_modules/')
import alipy
#do this stuff down here so IRAF doesn't save any parameters, and to make important tasks avaliable 
iraf.prcacheOff()
iraf.imred()
iraf.ccdred()
#centerpars
centerpars=iraf.centerpars.getParDict()
centerpars['calgorithm'].set('centroid')
centerpars['cbox'].set('10')
centerpars['cthreshold'].set('0')
centerpars['minsnratio'].set('1')
centerpars['cmaxiter'].set('10')
centerpars['maxshift'].set('5')
centerpars['clean'].set('no')
centerpars['rclean'].set('1')
centerpars['rclip'].set('2')
centerpars['kclean'].set('3')
centerpars['mkcenter'].set('yes')

#datapars
datapars=iraf.datapars.getParDict()
datapars['scale'].set('1')
datapars['fwhmpsf'].set('5')
datapars['emission'].set('yes')
datapars['sigma'].set('INDEF')
datapars['datamin'].set('-500')
datapars['datamax'].set('30000')
datapars['noise'].set('poisson')
datapars['readnoise'].set('6.5')
datapars['epadu'].set('2.3')
datapars['exposure'].set('EXPTIME')
datapars['airmass'].set('SECZ')
datapars['filter'].set('CCDFLTID')
datapars['obstime'].set('JD')

#findpars
findpars=iraf.findpars.getParDict()
findpars['threshold'].set('4.0')
findpars['nsigma'].set('1.5')
findpars['ratio'].set('1')
findpars['theta'].set('0')
findpars['sharplo'].set('0.2')
findpars['sharphi'].set('1.')
findpars['roundlo'].set('-1.')
findpars['roundhi'].set('1.')
findpars['mkdetections'].set('no')

#skypars
skypars=iraf.fitskypars.getParDict()
skypars['salgorithm'].set('mode')
skypars['annulus'].set('25.')
skypars['dannulus'].set('7.')
skypars['skyvalue'].set('0.')
skypars['smaxiter'].set('10')
skypars['sloclip'].set('0.')
skypars['shiclip'].set('0.')
skypars['snreject'].set('50')
skypars['sloreject'].set('3.')
skypars['shireject'].set('3.')
skypars['khist'].set('3.')
skypars['binsize'].set('0.1')
skypars['smooth'].set('no')
skypars['rgrow'].set('0.')
skypars['mksky'].set('no')

#photpars
photpars=iraf.photpars.getParDict()
photpars['weighting'].set('constant')
photpars['apertures'].set('9')
photpars['zmag'].set('25.')
photpars['mkapert'].set('no')

def alignReduced(color,images_to_align):
	'''align the flatten images'''
	#grab the paths to the sky subtracted and flattened images

	#images_to_align =sorted(glob.glob("reduced/*"+color+"*.fits"))

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

def photometry(color, images):
	#grab the aligned images
	#images=sorted(glob.glob('reduced/'+color+'align/*fits'))

	for i in images:
		iraf.phot(i, coords='reduced/'+color+'align/coords.lis',
			fwhmpsf=3,datamin=-500.,datamax=10000.,readnoise=20.,epadu=7.2,
			  exposur="EXPTIME",airmass="SECZ",obstime="JD",filter="IRFLTID",annulus=15,
		  	  dannulu=7, apertur="9",verify='no',output=i+".MC")
	return



#function reads open photometry files and looks up the quantities we're interested in, like magnitude, error, jd, airmass
#then takes this data and puts it in a pandas data frame
def magtodf(color):
    magfiles=glob.glob('reduced/'+color.upper()+'align/*'+color.upper()+'*.MC')
    
    #the keys for this dictionary will be the columns for the data frame.
    #each key starts off with an empy python list as its value.
    #we will read each output file one by one and append its data to the appropriate lists
    #so that each element in the list for a key will represents a row in that column 
    rowdict={'fname':[],'date':[],'juliandate':[],'airmass':[],
    	'mag1':[],'mag2':[],'mag3':[],'mag4':[],'mag5':[], 'mag6':[],
    	'mag7':[],'merr1':[], 'merr2':[], 'merr3':[], 'merr4':[], 'merr5':[], 'merr6':[], 'merr7':[]}

    for i in magfiles:
		#use the handy astropy ascii object to read photometry files
		photdata=ascii.read(i)
		#the astropy.ascii automatically masks any bad data values. I'd prefer to keep the bad values as np.nans
		if np.ma.is_masked(photdata['MAG']):
			photdata['MAG'][photdata['MAG'].mask]=np.nan
		if np.ma.is_masked(photdata['MERR']):
			photdata['MERR'][photdata['MERR'].mask]=np.nan
		#for append the data from this photometry file to the dictionary
		rowdict['fname'].append(photdata['IMAGE'][0])
		rowdict['date'].append(float(photdata['IMAGE'][0][0:6]))
		rowdict['juliandate'].append(photdata['OTIME'][0])
		rowdict['airmass'].append(photdata['XAIRMASS'][0])
		rowdict['mag1'].append(photdata['MAG'][0])
		rowdict['mag2'].append(photdata['MAG'][1])
		rowdict['mag3'].append(photdata['MAG'][2])
		rowdict['mag4'].append(photdata['MAG'][3])
		rowdict['mag5'].append(photdata['MAG'][4])
		rowdict['mag6'].append(photdata['MAG'][5])
		rowdict['mag7'].append(photdata['MAG'][6])
		rowdict['merr1'].append(photdata['MERR'][0])
		rowdict['merr2'].append(photdata['MERR'][1])
		rowdict['merr3'].append(photdata['MERR'][2])
		rowdict['merr4'].append(photdata['MERR'][3])
		rowdict['merr5'].append(photdata['MERR'][4])
		rowdict['merr6'].append(photdata['MERR'][5])
		rowdict['merr7'].append(photdata['MERR'][6])
    
    #create a pandas dataframe out of the dictionary
    df=pd.DataFrame(rowdict)
    #change the data type of the date column to int. cant translate from string to int above for some reason
    df['date']=df['date'].astype(int)

    if color.upper()=='J':
    	Jphot=df
    	Jphot['Cal']=Jphot.mag1 - ((Jphot.mag2 + Jphot.mag3 + Jphot.mag4 + Jphot.mag5 + Jphot.mag6+ Jphot.mag7)/6.0) + 15.154
    	Jphot.to_pickle('Jphot.pkl')
    	return Jphot
    elif color.upper()=='H':
    	Hphot=df
    	Hphot['Cal']=Hphot.mag1 - ((Hphot.mag2 + Hphot.mag3 + Hphot.mag4 + Hphot.mag5 + Hphot.mag6+ Hphot.mag7)/6.0) + 14.559
    	Hphot.to_pickle('Hphot.pkl')
    	return Hphot
    else:
    	print 'I can only calibrate J or H data. Here is your raw data'
    	return df

def lightCurve():
	Jphot=pd.read_pickle('Jphot.pkl')
	Hphot=pd.read_pickle('Hphot.pkl')

	fig=plt.figure()

	ax1=fig.add_subplot(211)
	ax1.errorbar(Jphot.juliandate.astype(float)-2450000, Jphot.Cal, yerr=Jphot.merr1, fmt='bo', label="J")
	ax1.invert_yaxis()
	plt.legend()

	ax2=fig.add_subplot(212)
	ax2.errorbar(Hphot.juliandate.astype(float)-2450000, Hphot.Cal, yerr=Hphot.merr1, fmt='ro', label='H')
	ax2.invert_yaxis()
	plt.legend()
	
	plt.show()

	return