# This function creates a new "elec_recon_persyst" subfolder in a patient's freesurfer directory so that
#  BIDS-iEEG functions can use that folder for creating a BIDS-iEEG structured folder. Key files are copied from
# the elec_recon folder. The only file that is changes i *.electrodeNames, which is replaced with Persyst lay file names

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
    print('Usage: createLayElecRecon.py sub_id (e.g., createLayElecRecon.py TWH018_layChan.tsv)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: createLayElecRecon.py requires 1 argument: TWH018_layChan.tsv')

# Import Parameter(s) from command line
layFname=sys.argv[1]
sub = layFname.split('_')[0]

#fsdir='/Applications/freesurfer/subjects'
fsdir=os.environ['SUBJECTS_DIR']
chanMapDir='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/LAY2IELVIS_MAPS' #TODO get this somewhere?

# Load mapping between iELVis and lay filenames if it exists
lay2ielvisFname=os.path.join(chanMapDir,sub+"_lay2ielvis.tsv")
if os.path.exists(lay2ielvisFname):
    print('Importing lay<->iELVis channel mapping from %s' % lay2ielvisFname)
    lay2ielvisDf=pd.read_csv(lay2ielvisFname, sep='\t', header=0)
    print(lay2ielvisDf.head())
    chanMapping=dict()
    for ct, chan in enumerate(lay2ielvisDf['iELVisChanName']):
        chanMapping[chan]=lay2ielvisDf['layChanName'][ct]
    print('The channel mapping is:')
    print(chanMapping)
else:
    print('%s does not exist. Need to create it.' % lay2ielvisFname)
    exit()


### CREATE NEW elec_recon_persyst FOLDER AND COPY FILES OVER

# Create new elec_recon folder
layFolder=os.path.join(fsdir,sub,'elec_recon_persyst')
if not os.path.isdir(layFolder):
    os.mkdir(layFolder)

# Copy coordinate files over
ielvisFolder=os.path.join(fsdir,sub,'elec_recon')
extList=['LEPTO','LEPTOVOX','PIAL','PIALVOX','POSTIMPLANT','FSAVERAGE','INF','mgrid']
for ext in extList:
    fname=sub+'.'+ext
    copyfile(os.path.join(ielvisFolder,fname),os.path.join(layFolder,fname))

# Copy nii.gz files over
for fname in os.listdir(ielvisFolder):
    if 'nii.gz' in fname:
        print("copying over %s" % fname)
        copyfile(os.path.join(ielvisFolder,fname),os.path.join(layFolder,fname))

# import channel names from iELVis
ielvisChanNameFname=os.path.join(fsdir,sub,'elec_recon',sub + '.electrodeNames')
print("Importing iELVis channel names from {}".format(ielvisChanNameFname))
ielvisDf=pd.read_csv(ielvisChanNameFname,sep=' ',header=1)
ielvisDf.head()
dfHdr=list(ielvisDf)
ielvisNames=list(ielvisDf[dfHdr[0]])
print("%d iELVis channels found" % len(ielvisNames))
checkUnique(ielvisNames)

# import channel names from lay file (NOT importing data)
[eegHdr, eegData]=lr.layread(layFname,importDat=False)
layChanMap=eegHdr['rawheader']['channelmap']
layNames=lr.get_eeg_chan_names(eegHdr['rawheader']['channelmap'])
nLayChan=len(layNames)
print("%d lay channels found" % nLayChan)
checkUnique(layNames)


# Try to find an iELVis channel name for each lay channel and vice versa
ielvisNamesMissed=list()
layNamesUsed=list()
layNamesLower=list()
iel2layFullDict=dict()
for tempName in layNames:
    layNamesLower.append(tempName.lower())
for ielChan in ielvisNames:
    if ielChan in list(chanMapping.keys()):
        layNamesUsed.append(chanMapping[ielChan])
        iel2layFullDict[ielChan]=chanMapping[ielChan]
    elif ielChan.lower() in layNamesLower:
        layId=layNamesLower.index(ielChan.lower())
        layNamesUsed.append(layNames[layId])
        iel2layFullDict[ielChan]=layNames[layId]
    else:
        ielvisNamesMissed.append(ielChan)
print('iELVis names without Lay partner:')
print(ielvisNamesMissed)
print('Lay names without iELVis partner:')
layNamesMissed=np.setdiff1d(layNames,layNamesUsed)
print(layNamesMissed)
if (len(ielvisNamesMissed)>0) or (len(layNamesMissed)>0):
    print("Exiting. You need to solve missed names by editting %s " % lay2ielvisFname)

# Create new electrode names file
elecNameFname=sub+'.electrodeNames'
outFname=os.path.join(layFolder,elecNameFname)
inFname=os.path.join(ielvisFolder,elecNameFname)
fIn = open(inFname, 'r')
lines = fIn.readlines()
fIn.close()
fOut=open(outFname,'w')
# Write header
fOut.write(lines[0])
fOut.write(lines[1])
for line in lines[2:]:
    splitLine=line.split(' ')
    fOut.write(iel2layFullDict[splitLine[0]]+' '+splitLine[1]+' '+splitLine[2])
fOut.close()

# Create new anatomical labels file
anatFname=sub+'_DK_AtlasLabels.tsv'
inFname=os.path.join(ielvisFolder,anatFname)
outFname=os.path.join(layFolder,anatFname)
fIn = open(inFname, 'r')
lines = fIn.readlines()
fIn.close()
fOut=open(outFname,'w')
for line in lines:
    splitLine=line.split('\t')
    fOut.write(iel2layFullDict[splitLine[0]]+'\t'+splitLine[1])
fOut.close()


print('createLayElecRecon.py completed successfully!!!')