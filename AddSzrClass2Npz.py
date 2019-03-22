import inifile
import numpy as np
import pandas as pd
from datetime import datetime
import os
import sys

####### HELPER FUNCS

def createSzrDf(patient_id,dataRootDir,implantDateDt):
    # subnum = '081'
    # implantDateStr = getImplantDate(subnum)
    # implantDateDt = datetime.strptime(implantDateStr, '%m/%d/%Y')
    # dataRootDir = '/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PY_DATA/TWH081/'
    # patient_id = 'TWH' + subnum
    szrTsvFname = patient_id + '_szrs.tsv'
    szrTsvFnameFull = os.path.join(dataRootDir, szrTsvFname)
    subnum = patient_id[3:]
    # Import researcher-derived szr onset/offset info
    (szrOnsetDt, szrOffsetDt, szrType) = import_szr_info(subnum)
    # Convert szr onset and offset times into the # of seconds since midnight on the day of the implant
    # since that corresponds to time 0 in secondsSinceImplant
    nSzr = len(szrOnsetDt)
    print('%d szrs found' % nSzr)
    szrOnsetSec = np.zeros(nSzr)
    szrOffsetSec = np.zeros(nSzr)
    emptyList = []
    for a in range(nSzr):
        szrOnsetSec[a] = (szrOnsetDt[a] - implantDateDt).total_seconds()
        szrOffsetSec[a] = (szrOffsetDt[a] - implantDateDt).total_seconds()
        emptyList.append('')

    tempDict = {'OnsetInSecFromImplant': szrOnsetSec, 'OffsetInSecFromImplant': szrOffsetSec,
                'SzrType': szrType, 'AppearsInTheseFiles': emptyList}
    szrDf = pd.DataFrame(data=tempDict)
    return szrDf, szrTsvFnameFull

def getSzrClass(secondsSinceImplant,szrDf,npzFname):
    nTpt=len(secondsSinceImplant)
    szrClass=np.zeros(nTpt) # 0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type

    nSzr=szrDf.shape[0]
    uniqSzrIds=[]
    # Loop over all time points to see if they lie within a szr
    for a in range(nTpt):
        szrId=inSzr(secondsSinceImplant[a],szrDf['OnsetInSecFromImplant'],szrDf['OffsetInSecFromImplant'])
        if szrId>0:
            szrClass[a] =szrType2Num(szrDf['SzrType'][szrId])
            if szrId not in uniqSzrIds:
                uniqSzrIds.append(szrId)
    # Update szr data frame to indicate which szrs occurred in this file (if any)
    print('uniqSzrIds {}'.format(uniqSzrIds))
    for szrId in uniqSzrIds:
        if len(szrDf['AppearsInTheseFiles'][szrId])>0:
            szrDf.loc[szrId, 'AppearsInTheseFiles'] = szrDf.loc[szrId, 'AppearsInTheseFiles']+', '+npzFname
        else:
            szrDf.loc[szrId, 'AppearsInTheseFiles']=npzFname
    return szrClass

# def getSzrClass(secondsSinceImplant,subnum,implantDateDt):
#     nTpt=len(secondsSinceImplant)
#     szrClass=np.zeros(nTpt) # 0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
#     (szrOnsetDt, szrOffsetDt, szrType) = import_szr_info(subnum)
#
#     # Convert szr onset and offset times into the # of seconds since midnight on the day of the implant
#     # since that corresponds to time 0 in secondsSinceImplant
#     nSzr=len(szrOnsetDt)
#     szrOnsetSec=np.zeros(nSzr)
#     szrOffsetSec=np.zeros(nSzr)
#     for a in range(nSzr):
#         szrOnsetSec[a]=(szrOnsetDt[a]-implantDateDt).total_seconds()
#         szrOffsetSec[a] = (szrOffsetDt[a] - implantDateDt).total_seconds()
#     # Loop over all time points to see if they lie within a szr
#     for a in range(nTpt):
#         szrId=inSzr(secondsSinceImplant[a],szrOnsetSec,szrOffsetSec)
#         if szrId>0:
#             szrClass[a]=szrType2Num(szrType[szrId])
#     return szrClass


def szrType2Num(szrTypeStr):
    #0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
    szrType=3
    if szrTypeStr.lower()=='clinical':
        szrType=1
    elif szrTypeStr.lower()=='electrographic':
        szrType = 2
    else:
        print('Warning unknown szr type, %s, in patient *_SzrOnset.tsv file' % szrTypeStr.lower())
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
patient_id='TWH'+subnum
eegFiles=list()
print('Found the following iEEG data files:')
for f in os.listdir(dataRootDir):
    if f.endswith('.npz') and f.startswith(patient_id):
        print(f)
        eegFiles.append(f)
print('%d files found' % len(eegFiles))

implantDateStr = getImplantDate(subnum)
implantDateDt = datetime.strptime(implantDateStr, '%m/%d/%Y')
(szrDf, szrDfFnameFull)=createSzrDf(patient_id,dataRootDir,implantDateDt)
# print(szrDf)
# print(szrDfFnameFull)
# print(szrDf['OffsetInSecFromImplant'] - szrDf['OnsetInSecFromImplant'])
# print('PICKUP APPLY THIS TO AN NPZ THAT CONTAINS SZR')
# print(eegFiles[12])
# exit()

# Loop over npz files containing iEEG data
for f in eegFiles:
#for f in eegFiles[12:13]:
    print('Adding szr class time series to %s' % f)
    npzFnameFull=os.path.join(dataRootDir,f)
    justFname=npzFnameFull.split('/')[-1]
    tempFname='temp_'+justFname
    print('Moving original file to %s' % tempFname)
    os.rename(npzFnameFull,tempFname)
    npz=np.load(tempFname)

    #szrClass=getSzrClass(npz['seconds_since_implant'],subnum,implantDateDt)
    szrClass = getSzrClass(npz['seconds_since_implant'], szrDf, justFname)

    # Save seizure data frame as tsv in case it has been changed
    print('Saving seizure info to %s' % szrDfFnameFull)
    szrDf.to_csv(szrDfFnameFull,sep='\t',index=False)
    szrDf.to_pickle("tempSzrDf.pkl")

    np.savez(npzFnameFull,
            ieeg=npz['ieeg'],
            chan_names=npz['chan_names'],
            time_of_day_sec=npz['time_of_day_sec'],
            seconds_since_implant=npz['seconds_since_implant'],
            srate_hz=npz['srate_hz'],
            lay_fname=npz['lay_fname'],
            patient_id=npz['patient_id'],
            szr_class=szrClass,
            days_since_implant=npz['days_since_implant'])

    print('Removing temp file')
    os.remove(tempFname)

print('Done!!!')