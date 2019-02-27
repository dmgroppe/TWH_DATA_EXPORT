# This code reads the channel names from all lay files to see make sure the names are all the same
# It also checks to make sure all channel names are unique. If any lay files have different montages the
# user can move them into a subdirectory so that they are not processed further.

import numpy as np
import pandas as pd
import os
import sys
import layread as lr


def checkUnique(nameList):
    allUnique=True
    if len(nameList)==len(np.unique(nameList)):
        print("All channels have unique names.")
    else:
        allUnique=False
        raise Exception('Two or more channels have the exact same name.')


# Start of main function
if len(sys.argv) == 1:
    print('Usage: checkLayChanNamesAllClips.py subName (e.g., checkLayChanNamesAllClips.py TWH081)')
    exit()
if len(sys.argv) != 2:
    raise Exception('Error: checkLayChanNamesAllClips.py requires 1 argument: subName')

# Import Parameters from json file
sub = sys.argv[1]
print('Checking channel name consistency for %s' % sub)

#rootDir="/Volumes/Seagate Expansion Drive/PersystFormat/TWH081"
rootDir=os.path.join('/media/dgroppe/Seagate Expansion Drive/PersystFormat/',sub)
lay_fnames=list()
for f in os.listdir(rootDir):
    if f.endswith('.lay'):
        lay_fnames.append(f)
print('%d lay files found' % len(lay_fnames))

# Get channel names from first file
[eegHdr, eegData]=lr.layread(os.path.join(rootDir,lay_fnames[0]),importDat=False)
layChanMap=eegHdr['rawheader']['channelmap']

# Make sure channel names are unique
checkUnique(layChanMap)

# Loop over remaining lay files to see if channel names are compatible
altChanMaps=list()
altChanMapFnames=list()
for f in lay_fnames[1:]:
    [eegHdr, eegData]=lr.layread(os.path.join(rootDir,f),importDat=False)
    tempLayChanMap=eegHdr['rawheader']['channelmap']
    if tempLayChanMap!=layChanMap:
        print('Channel names in file %s NOT the Same!' % f)
        altChanMaps.append(tempLayChanMap.copy())
        altChanMapFnames.append(f)
        if len(tempLayChanMap)==len(layChanMap):
            print('They have the same # of chans')
        else:
            print('They do NOT have the same # of chans')
    else:
        print('Same!')

# Print channel names side by side for each file that doesn't match the first file
nAltChanMaps=len(altChanMaps)
if nAltChanMaps>0:
    for id in range(nAltChanMaps):
        print('AltMap file #%d %s' % (id,altChanMapFnames[id]))
        print('FirstLayFile\tAltMap')
        for a in range(len(layChanMap)):
            print('%s\t%s' % (layChanMap[a],altChanMaps[id][a]))
        print()

    # Ask user if mismatched channel names should be moved to a new directory
    print('Should the %d files with channel names that do not match first file be moved to a subdirectory?' % len(altChanMaps))
    resp=input('y/n: ')
    if resp=='y':
        newDir=os.path.join(rootDir,'DIF_CHAN_NAMES')
        try:
            os.mkdir(newDir)
        except OSError:
            print ("Creation of the directory %s failed" % newDir)
        else:
            print ("Successfully created the directory %s " % newDir)
        print('Moving the files to %s' % newDir)
        for f in altChanMapFnames:
            os.rename(os.path.join(rootDir,f), os.path.join(newDir,f))
    else:
        print('Not moving!')
