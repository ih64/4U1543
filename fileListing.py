import numpy as np
import pandas as pd 
from pyraf import iraf
import sys, StringIO

def hselToDf(color,frameFlavor='raw'):
	'''
	this function packs the file name, observation time, and YYMMDD date 
	of smarts fits files into a pandas data frame
	color is either 'J' or 'H', the broadbandfilter you're interested in
	if frameFlavor='raw' this function is hard coded to look in either the Hraw/ or Jraw/
	if frameFlavor='flat' this function is hard coded to look in irflats/
	it then pickles the data frame
	'''
	#prepare a file handle. this will be a temporary storing space for the data
	fileHandle=StringIO.StringIO()
	#use iraf hselect to spit out file name and obs time for all files
	#save in the file handle
	if frameFlavor=='raw':
		iraf.hselect(color.upper()+"raw/*fits", fields='$I,JD', expr='yes', Stdout=fileHandle)
	elif frameFlavor=='flat':
		iraf.hselect("irflats/*"+color.lower()+"*fits", fields='$I,JD', expr='yes', Stdout=fileHandle)
	else:
		print "use either 'raw' or 'flat' for frameFlavor variable"
		return

	fileHandle.seek(0)
	#stick the file handle into a pandas parser to read it into a data frame
	fileTable=pd.io.parsers.read_fwf(fileHandle, names=['file','JulianDate'])
	fileHandle.close()

	#Try to force the JulianDate data to floats. This wont work if its corrupted somehow,
	#or has a bad value printed, like a string.
	try:
		fileTable['JulianDate']=fileTable['JulianDate'].astype(float)
		#grab the YYMMDD dates from the file name and list these in a column
		if frameFlavor=='raw':
			fileTable['Date']=fileTable.file.apply(lambda i: i[-16:-10]).astype(int)
			#check for nulls in the dataframe
			if checkNullColumn(fileTable):
				#pickle the data frame
				fileTable.to_pickle(color.upper()+'rawList.pkl')
				return
			else:
				return
		else:
			if checkNullColumn(fileTable):
				fileTable['Date']=fileTable.file.apply(lambda i: i[-17:-11]).astype(int)
				#pickle the data frame
				fileTable.to_pickle(color.upper()+'flatList.pkl')	
				return
			else:
				return
	except ValueError:
		print "encountered a value error. There is a bad value in either the JD field of a header, or a nonstandard filename"
		print "fix these and try again"
		return

def checkNullColumn(df):
	columns=df.columns
	for name in columns:
		if df[name][pd.isnull(df[name])].size > 0:
			print "found nulls in the data set"
			print df.ix[df[name][pd.isnull(df[name])].index]
			print "fix these and try again"
			return False
		else:
			return True

if __name__ =='__main__':
	hselToDf(str(sys.argv[1]), frameFlavor=str(sys.argv[2]))