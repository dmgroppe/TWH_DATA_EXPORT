""" This script creates a text file of channel names from a lay file. The first line of the text file is the name of lay file
from which the labels were taken."""
import numpy as np
import pandas as pd
import os
import layread as lr
from shutil import copyfile
import sys

def checkUnique(nameList):
    allUnique=True
    if len(nameList)==len(np.unique(nameList)):
        print("All channels have unique names.")
    else:
        allUnique=False
        raise Exception('Two or more channels have the exact same name.')


###### Start of main function
if len(sys.argv)==1:
    print('Usage: createLayElecRecon.py sub_id (e.g., createLayElecRecon.py TWH018)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: createLayElecRecon.py requires 1 argument: sub_id')

# Import Parameter(s) from command line
layFnameFull=sys.argv[1]
layFname=layFnameFull.split('/')[-1]
patientId=layFname.split('_')[0]
print('Creating txt file of lay file channels for %s' % patientId)

# import channel names from lay file (NOT importing data)
[eegHdr, eegData]=lr.layread(layFnameFull,importDat=False)
layChanMap=eegHdr['rawheader']['channelmap']
layNames=lr.get_eeg_chan_names(eegHdr['rawheader']['channelmap'])
nLayChan=len(layNames)
print("%d lay channels found" % nLayChan)
checkUnique(layNames)

outFname=patientId+'_layChan.txt'
#outDir='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/LAY2IELVIS_MAPS'
outDir='LAY2IELVIS_MAPS'
outFnameFull=os.path.join(outDir,outFname)
print('Creating %s' % outFnameFull)
fid=open(outFnameFull,'w')
fid.write(layFname+"\n")
for chanName in layNames:
    fid.write(chanName+"\n")
fid.close()
