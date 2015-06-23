import numpy as np
import pandas as pd 
from pyraf import iraf
import sys, StringIO

def hselToDf(color):
	'''
	this function packs the file name, observation time, and YYMMDD date 
	of smarts fits files into a pandas data frame
	color is either 'J' or 'H', the broadbandfilter you're interested in
	this function is hard coded to look in either the Hraw/ or Jraw/ 
	directories for fits files.
	it then pickles the data frame
	'''
	#prepare a file handle. this will be a temporary storing space for the data
	fileHandle=StringIO.StringIO()
	#use iraf hselect to spit out file name and obs time for all files
	#save in the file handle
	iraf.hselect(color+"raw/*fits", fields='$I,JD', expr='yes', Stdout=fileHandle)
	fileHandle.seek(0)
	#stick the file handle into a pandas parser to read it into a data frame
	fileTable=pd.io.parsers.read_fwf(fileHandle, names=['file','JulianDate'])
	fileHandle.close()
	#grab the YYMMDD dates from the file name and list these in a column
	fileTable['Date']=fileTable.file.apply(lambda i: i[-16:-10]).astype(float)
	#pickle the data frame
	fileTable.to_pickle(color+'fileList.pkl')
	return

if __name__ =='__main__':
	hselToDf(str(sys.argv[1]))