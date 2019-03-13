""" This function takes a lay file (Persyst data file), removes bad channels, converts to avg ref, and saves
the data to disk in max-1 hour clips. Annotations are also saved."""

import numpy as np
import os
import sys
import pandas as pd
import layread as lr
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import scipy.signal as sig
import re
import pickle
import scipy.io as sio
from datetime import datetime

##### USEFUL FUNCTIONS #####
def import_szr_info(patient_id):
    """ Import seizure onset/offset as date time variables and szr type (clinical, electrographic, or unspecified) from
     a tsv file that has been produced from the master Excel spreadsheet"""

    # Import tsf file of onset/offset times & szr types TODO make path relative or an arg
    szrTimeFname = "/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PRIVATE/SZR_TIMES/TWH081_SzrOnset.tsv"
    szrTimeDf = pd.read_csv(szrTimeFname, sep='\t')

    # Collect Szr Types
    szrType = list()
    for szr in szrTimeDf['class']:
        szrType.append(szr)
    print(szrType)

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

    print(szrOnsetDt)
    print(szrOffsetDt)
    return szrOnsetDt, szrOffsetDt, szrType


def rm_bad_chans(patient_id,ieeg,chan_names):
    """ Load names of artifact ridden channels from text file and removes them. Text file should be in
    BAD_CHANS subdirectory and called something like TWH001_bad_chans.txt
    If the channel names ends in "?", that means it may have usable data
     Inputs:
       patient_id: string (e.g., 'TWH001')
       ieeg: numpy matrix of iEEG data
       chan_names: list of channel names

     Outputs:
       ieeg: numpy matrix of iEEG data with bad channels removed
       chan_names: list of channel names with bad channels removed"""

    in_fname=os.path.join('BAD_CHANS',patient_id+'_bad_chans.txt')
    if os.path.isfile(in_fname):
        df=pd.read_csv(in_fname,header=None)
        bad_chan_names=list() # List of clearly bad channels
        if df.iloc[0,0].lower()=='none':
            print('No artifact ridden channels for this participant.')
        else:
            for chan in df.iloc[:,0]:
                if chan[-1]!='?':
                    bad_chan_names.append(chan)
            print('Artifact ridden channels are: {}'.format(bad_chan_names))
        # TODO throw error if a bad channel listed that is not in chan_names
        # Get ids of good channels
        keep_ids=list()
        keep_chan_names=list()
        n_chan, n_tpt=ieeg.shape
        for c in range(n_chan):
            if not (chan_names[c] in bad_chan_names):
                keep_ids.append(c)
                keep_chan_names.append(chan_names[c])
        # Remove channels from data and channel names
        print('Removing %d poor quality channels' % (n_chan-len(keep_ids)))
        ieeg=ieeg[keep_ids,:]
        chan_names=keep_chan_names
    else:
        print('Could not find %s, which lists artifactual channels' % in_fname)
    return ieeg, chan_names


def inSzr(timePt,szrOnsetSec,szrOffsetSec):
    """ Also Yo """
    nSzr=len(szrOnsetSec)
    szrId=0
    for a in range(nSzr):
        if (timePt>=szrOnsetSec[a]) and (timePt<=szrOffsetSec[a]):
            szrId=a
            break
    return szrId


def getSzrClass(secondsSinceImplant,subnum,implantDateDt):
    """ Yo. PICKUP HERE """
    nTpt=len(secondsSinceImplant)
    szrClass=np.zeros(nTpt) # 0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
    (szrOnsetDt, szrOffsetDt, szrType) = import_szr_info(subnum)

    # Convert szr onset and offset times into the # of seconds since midnight (I think) on the day of the implant
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

def szrType2Num(szrTypeStr):
    #0=non-szr, 1=clinical szr, 2=subclinical szr, 3=szr of unknown type
    szrType=3
    if szrTypeStr.lower=='clinical':
        szrType=1
    elif szrTypeStr.lower=='electrographic':
        szrType = 2
    else:
        print('Warning unknown szr type, %s, in patient *_SzrOnset.tsv file' % szrTypeStr)

# not gold standard but can help double check
def get_szr_class_from_annotations(annot, n_tpt):
    """ Creats a numpy array that indicates for each time point if it is in a seizure or not according to annotations.
     onset_text and offset_text lists below indicate the annotation strings used to mark seizure onset and offset.
     Inputs:
        annot: The dict of lay file annotations
        n_tpt: The number of time points in the clip"""

    # Note, I assume that annotations in annot ordered from earliest to latest occurrence
    # TODO: double check
    # TODO: makes this use three values 0, 1, 2 for non-seizure, subclinical seizure, and clinical seizure
    szr_class = np.zeros(n_tpt, dtype='int8')  # default=no seizures
    onset_text = ['szr onset', 'sz onset']
    offset_text = ['szr offset', 'sz offset']

    annot_text = list()
    for a in annot:
        temp = a['text'].lower()
        annot_text.append(temp.rstrip('\n'))

    # Find out if offset occurs before onset
    offset_first = -1  # -1 means no seizure onsets OR offset
    for a in annot_text:
        if a in offset_text:
            offset_first = 1
            szr_class = szr_class + True
            break
        elif a in onset_text:
            offset_first = 0
            break

    if offset_first > -1:
        # There are seizures in the file
        print('# of seizures>=1 in these data')
        for ct, a in enumerate(annot):
            if annot_text[ct] in onset_text:
                # Szr onset
                szr_class[a['sample']:] = True
            elif annot_text[ct] in offset_text:
                # Szr offset
                szr_class[a['sample']:] = False
    else:
        print('No szrs found in these data')
    return szr_class


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
        print("Implant date is %s" % implantDate)
    return implantDate


### START OF MAIN FUNCTION ###
if len(sys.argv)==1:
    print('Usage: lay2npz.py lay_file_and_path subnum')
    exit()
if len(sys.argv)!=3:
    raise Exception('Error: lay2npz.py requires 2 arguments: lay_file_and_path subnum')

# Import Parameters from json file
lay_fname=sys.argv[1]
subnum=sys.argv[2]

# Load file
#lay_fname='/media/dgroppe/ValianteLabEuData/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
#lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
# short clip for code testing
#lay_fname='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/DATA_SBOX/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'

# 1 day clip with 3 szrs
#lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA_LONG/TWH056/TWH056_ShGa_dbf43bc5-601b-4e71-9b2d-175ea763242f-archive.lay'

[hdr, ieeg]=lr.layread(lay_fname,importDat=True)
#[hdr, ieeg]=lr.layread(lay_fname,importDat=False) # TODO undo false, just using false for developing
# TODO remove this!!!!
#ieeg=np.zeros((125,1000))
[n_chan, n_tpt]=ieeg.shape
print('%d timepoints read (i.e., %f hours)' % (n_tpt,n_tpt/(3600*hdr['samplingrate'])))
print('Total # of channels: %d' % n_chan)

# Save header information
clip_hdr=dict()
clip_hdr['srate_hz']=hdr['samplingrate']
clip_hdr['source_file']=hdr['datafile'].split('/')[-1]
clip_hdr['patient_id']=clip_hdr['source_file'].split('_')[0]
clip_hdr['channel_names']=hdr['rawheader']['channelmap']

# Remove unused channels (e.g., c101)
ieeg, clip_hdr['channel_names']=lr.rm_c_chans(ieeg,clip_hdr['channel_names'])

# Remove event channel
ieeg, clip_hdr['channel_names']=lr.rm_event_chan(ieeg,clip_hdr['channel_names'])

# Remove "-ref" from channel names
print('Removing "-ref" suffix from channel names ')
clip_hdr['channel_names']=lr.tidy_chan_names(clip_hdr['channel_names'])

# Remove artifactual channels TODO remove this?
ieeg, clip_hdr['channel_names']=rm_bad_chans(clip_hdr['patient_id'],ieeg,clip_hdr['channel_names'])

# Convert Data to Avg Ref TODO remove this?
# ieeg, ieeg_mn=lr.avg_ref(ieeg)

# Prune annotations TODO need to collect when szrs start/stop
clip_hdr['annotations']=lr.prune_annotations(hdr['annotations'])

# Get time in seconds corresponding to each time point
time_of_day_sec=lr.sample_times_sec(hdr['rawheader']['sampletimes'],n_tpt,1/hdr['samplingrate'])
print(len(time_of_day_sec))
print(time_of_day_sec[:5])

# Get day of recording relative to first date of electrode implantation
implant_day_str=getImplantDate(subnum)
implant_day_dt=datetime.strptime(implant_day_str,'%m/%d/%Y')

clip_day_str=hdr['starttime'].split(' ')[0]
clip_day_dt=datetime.strptime(clip_day_str,'%d-%b-%Y')
day_dlt_dt=clip_day_dt-implant_day_dt
days_since_implant=day_dlt_dt.days
seconds_since_implant=time_of_day_sec+day_dlt_dt.days*24*60*60

# Get start time without year
print("hdr starttime is {}".format(hdr['starttime']))
clip_hdr['starttime']=lr.starttime_anon(hdr['starttime'])
print('Start time is %s' % clip_hdr['starttime'])
print("This is %d day(s) since implantation" % days_since_implant)

# TODO Make szr_class 0,1, or 2 (1=subclinical szr, 2=clinical szr, 3=szr of unknown type)
#szr_class=get_szr_class(clip_hdr['annotations'],n_tpt)
#szr_class_annot=get_szr_class_from_annotations(clip_hdr['annotations'],n_tpt)
#should work: szr_class=getSzrClass(seconds_since_implant,subnum,implant_day_dt)
#print('sum szr_class=%d' % np.sum(szr_class))

# Have a separate output directory for each patient
out_path=os.path.join('PY_DATA',clip_hdr['patient_id'])
if os.path.isdir(out_path)==False:
    os.makedirs(out_path)

# Limit time_of_day_sec range to 0-24*3600
time_of_day_sec=time_of_day_sec%(24*3600)

# np.savez(os.path.join(out_path,'tempTWH081.npz'),
#          ieeg=ieeg,
#          time_of_day_sec=time_of_day_sec,
#          seconds_since_implant=seconds_since_implant,
#          srate_hz=clip_hdr['srate_hz'],
#          lay_fname=lay_fname,
#          days_since_implant=days_since_implant)
pickle.dump(clip_hdr,open(os.path.join(out_path,'tempTWH081.pkl'),'wb')) # TODO remove full date from header+annotations
# grab annotations for just the events in the clipped file

# Save data in 1 hour clips
clip_ct=0 # TODO, retrieve this from CSV?
cursor=0
n_tpt_per_hour=clip_hdr['srate_hz']*3600
subclip_ct=0
while cursor<n_tpt:
    print('Working on subclip %d' % subclip_ct)
    stop_id=np.min([n_tpt, cursor+n_tpt_per_hour])
    print('{} {}'.format(cursor,stop_id))
    # output file name of clip TODO add time of clip onset to ieeg_fname
    ieeg_fname=clip_hdr['patient_id']+'_Day-'+str(days_since_implant)+'_Clip-'+str(clip_ct)+'-'+str(subclip_ct)
    print('Saving clip %s' % ieeg_fname)
    # Save numeric data in NPZ format
    np.savez(os.path.join(out_path,ieeg_fname),
            ieeg=ieeg[:,cursor:stop_id],
            ieeg_mn=ieeg_mn[cursor:stop_id],
            szr_class=szr_class[cursor:stop_id],
            time_of_day_sec=time_of_day_sec[cursor:stop_id],
            srate_hz=clip_hdr['srate_hz'],
            days_since_implant=days_since_implant)

    # Save numeric data in MATLAB format
    # mat_dict=dict()
    # mat_dict['ieeg']=ieeg[:, cursor:stop_id]
    # mat_dict['ieeg_mn']=ieeg_mn[cursor:stop_id]
    # mat_dict['szr_class']=szr_class[cursor:stop_id]
    # mat_dict['time_of_day_sec']=time_of_day_sec[cursor:stop_id]
    # mat_dict['srate_hz']=clip_hdr['srate_hz']
    # sio.savemat(os.path.join(out_path,ieeg_fname), mat_dict)

    # Save header dict via pickle
    if subclip_ct==0:
        hdr_fname = clip_hdr['patient_id'] + '_Day-' + str(days_since_implant) + '_Clip-' + str(clip_ct)+'_hdr.pkl'
        pickle.dump(clip_hdr, open(os.path.join(out_path,hdr_fname), 'wb'))
    # TODO save header in a format that MATLAB can read?

    cursor=stop_id
    subclip_ct+=1

print('Done exporting Files')