import inifile
import numpy as np
import pandas as pd
from datetime import datetime
import os
import sys

####### HELPER FUNCS

def getSzrClass(secondsSinceImplant,subnum,implantDateDt):
    nTpt=len(secondsSinceImplant)
    szrClass=np.zeros(nTpt) # 0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
    (szrOnsetDt, szrOffsetDt, szrType) = import_szr_info(subnum)

    # Convert szr onset and offset times into the # of seconds since midnight on the day of the implant
    # since that corresponds to time 0 in secondsSinceImplant
    nSzr=len(szrOnsetDt)
    szrOnsetSec=np.zeros(nSzr)
    szrOffsetSec=np.zeros(nSzr)
    for a in range(nSzr):
        szrOnsetSec[a]=(szrOnsetDt[a]-implantDateDt).total_seconds()
        szrOffsetSec[a] = (szrOffsetDt[a] - implantDateDt).total_seconds()
    # Loop over all time points to see if they lie within a szr
    for a in range(nTpt):
        szrId=inSzr(secondsSinceImplant[a],szrOnsetSec,szrOffsetSec)
        if szrId>0:
            szrClass[a]=szrType2Num(szrType[szrId])
    return szrClass

#szrOnsetSec[a]=(szrOnsetDt[a]-implantDateDt).total_seconds()

def szrType2Num(szrTypeStr):
    #0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
    szrType=3
    if szrTypeStr.lower()=='clinical':
        szrType=1
    elif szrTypeStr.lower()=='electrographic':
        szrType = 2
    else:
        pass
        #print('Warning unknown szr type, %s, in patient *_SzrOnset.tsv file' % szrTypeStr.lower())
    return szrType

        
def inSzr(timePt,szrOnsetSec,szrOffsetSec):
    """ Also Yo """
    nSzr=len(szrOnsetSec)
    szrId=0
    for a in range(nSzr):
        if (timePt>=szrOnsetSec[a]) and (timePt<=szrOffsetSec[a]):
            szrId=a
            break
    return szrId

def import_szr_info(patient_id):
    """ Import seizure onset/offset as date time variables and szr type (clinical, electrographic, or unspecified) from
     a tsv file that has been produced from the master Excel spreadsheet"""

    # Import tsf file of onset/offset times & szr types
    szrTimeFname="PRIVATE/SZR_TIMES/TWH"+patient_id+"_SzrOnset.tsv"
    print("importing szr info from %s" % szrTimeFname)
    #szrTimeFname = "/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PRIVATE/SZR_TIMES/TWH081_SzrOnset.tsv"
    szrTimeDf = pd.read_csv(szrTimeFname, sep='\t')

    # Collect Szr Types
    szrType = list()
    for szr in szrTimeDf['class']:
        szrType.append(szr)
    # print(szrType)

    # Collect Szr Onset & Offset Times
    szrOnsetDt = list()
    szrOffsetDt = list()
    for ct, onsetDate in enumerate(szrTimeDf['actual date']):
        onsetTime = szrTimeDf['start time'][ct]
        offsetTime = szrTimeDf['end time'][ct]
        onsetDtStr = onsetDate + " " + onsetTime
        szrOnsetDt.append(datetime.strptime(onsetDtStr, '%Y-%m-%d %H:%M:%S'))
        offsetDtStr = onsetDate + " " + offsetTime
        szrOffsetDt.append(datetime.strptime(offsetDtStr, '%Y-%m-%d %H:%M:%S'))
        if datetime.strptime(offsetTime, '%H:%M:%S') < datetime.strptime(onsetTime, '%H:%M:%S'):
            # Seizure offset must be on the day after the onset
            szrOffsetDt += datetime.timedelta(days=1)

    # print(szrOnsetDt)
    # print(szrOffsetDt)
    return szrOnsetDt, szrOffsetDt, szrType

        
def getImplantDate(sub_num_str):
    # tsv file
    implantTsv = 'PRIVATE/UpcomingImplantCandidates.tsv'
    implantDf = pd.read_csv(implantTsv, sep='\t')

    implantDate = ""
    sub_id = 'TWH_' + sub_num_str
    row_bool = implantDf['TWRI ID'] == sub_id
    sum_bool = np.sum(row_bool)
    if sum_bool == 0:
        raise Exception("sub_id {} not found in {}".format(sub_id, implantTsv))
    elif sum_bool > 1:
        raise Exception("sub_id {} found more than once in {}".format(sub_id, implantTsv))
    else:
        implantDate = implantDf['Implant Date'][row_bool].values[0]
        # print("Implant date is %s" % implantDate)
    return implantDate


######## MAIN SCRIPT

if len(sys.argv)==1:
    print('Usage: AddSzrClass2Npz.py subnum (e.g, subnum=081)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: AddSzrClass2Npz.py requires 1 argument')

subnum=sys.argv[1]
dataRootDir='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PY_DATA/TWH'+subnum
prefix='TWH'+subnum
eegFiles=list()
print('Found the following iEEG data files:')
for f in os.listdir(dataRootDir):
    if f.endswith('.npz') and f.startswith(prefix):
        print(f)
        eegFiles.append(f)
print('%d files found' % len(eegFiles))

for f in eegFiles:
    print('Adding szr class time series to %s' % f)
    npzFname=os.path.join(dataRootDir,f)
    #npzFname='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PY_DATA/TWH081/TWH081_Day-9_Clip-0-0.npz'
    justFname=npzFname.split('/')[-1]
    tempFname='temp_'+justFname
    print('Moving original file to %s' % tempFname)
    os.rename(npzFname,tempFname)
    npz=np.load(tempFname)

    implantDateStr=getImplantDate(subnum)
    implantDateDt=datetime.strptime(implantDateStr,'%m/%d/%Y')
    szrClass=getSzrClass(npz['seconds_since_implant'],subnum,implantDateDt)

    # TODO get subnum from npz file
    #        subnum=subnum,
    np.savez(npzFname,
            ieeg=npz['ieeg'],
            chan_names=npz['chan_names'],
            time_of_day_sec=npz['time_of_day_sec'],
            seconds_since_implant=npz['seconds_since_implant'],
            srate_hz=npz['srate_hz'],
            lay_fname=npz['lay_fname'],
            subnum=npz['subnum'],
            szr_class=szrClass,
            days_since_implant=npz['days_since_implant'])

    print('Removing temp file')
    os.remove(tempFname)

print('Done!!!')