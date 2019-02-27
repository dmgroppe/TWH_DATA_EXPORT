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


def get_szr_class(annot, n_tpt):
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



### START OF MAIN FUNCTION ###
if len(sys.argv)==1:
    print('Usage: lay2npz.py lay_file_and path')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: lay2npz.py requires 1 argument: lay_file_and path')

# Import Parameters from json file
lay_fname=sys.argv[1]

# Load file
#lay_fname='/media/dgroppe/ValianteLabEuData/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
#lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
# short clip for code testing
#lay_fname='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/DATA_SBOX/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'

# 1 day clip with 3 szrs
#lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA_LONG/TWH056/TWH056_ShGa_dbf43bc5-601b-4e71-9b2d-175ea763242f-archive.lay'

[hdr, ieeg]=lr.layread(lay_fname)
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

# Remove artifactual channels
ieeg, clip_hdr['channel_names']=rm_bad_chans(clip_hdr['patient_id'],ieeg,clip_hdr['channel_names'])

# Convert Data to Avg Ref
ieeg, ieeg_mn=lr.avg_ref(ieeg)

# Prune annotations TODO need to collect when szrs start/stop
clip_hdr['annotations']=lr.prune_annotations(hdr['annotations'])

# Get time in seconds corresponding to each time point
time_of_day_sec=lr.sample_times_sec(hdr['rawheader']['sampletimes'],n_tpt,1/hdr['samplingrate'])

# Get day of recording relative to first date of electrode implantation
implant_day_str='10-Jun-2015' # TODO pass this as arg, have it in text file someplace
implant_day_dt=datetime.strptime(implant_day_str,'%d-%b-%Y')
clip_day_str=hdr['starttime'].split(' ')[0]
clip_day_dt=datetime.strptime(clip_day_str,'%d-%b-%Y')
day_dlt_dt=clip_day_dt-implant_day_dt
day_since_implant=day_dlt_dt.days

# Get start time without year
clip_hdr['starttime']=lr.starttime_anon(hdr['starttime'])
print('Start time is %s' % clip_hdr['starttime'])

# TODO Make szr_class 0,1, or 2 (1=subclinical szr, 2=clinical szr)
szr_class=get_szr_class(clip_hdr['annotations'],n_tpt)

# Have a separate output directory for each patient
out_path=os.path.join('PY_DATA',clip_hdr['patient_id'])
if os.path.isdir(out_path)==False:
    os.makedirs(out_path)

# Save data in 1 hour clips
clip_ct=0 # TODO, retrieve this from CSV?
cursor=0
n_tpt_per_hour=clip_hdr['srate_hz']*3600
subclip_ct=0
while cursor<n_tpt:
    print('Working on subclip %d' % subclip_ct)
    stop_id=np.min([n_tpt, cursor+n_tpt_per_hour])
    print('{} {}'.format(cursor,stop_id))
    ieeg_fname=clip_hdr['patient_id']+'_Day-'+str(day_since_implant)+'_Clip-'+str(clip_ct)+'-'+str(subclip_ct)
    print('Saving clip %s' % ieeg_fname)
    # Save numeric data in NPZ format
    np.savez(os.path.join(out_path,ieeg_fname),
            ieeg=ieeg[:,cursor:stop_id],
            ieeg_mn=ieeg_mn[cursor:stop_id],
            szr_class=szr_class[cursor:stop_id],
            time_of_day_sec=time_of_day_sec[cursor:stop_id],
            srate_hz=clip_hdr['srate_hz'],
            day_since_implant=day_since_implant)

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
        hdr_fname = clip_hdr['patient_id'] + '_Day-' + str(day_since_implant) + '_Clip-' + str(clip_ct)+'_hdr.pkl'
        pickle.dump(clip_hdr, open(os.path.join(out_path,hdr_fname), 'wb'))
    # TODO save header in a format that MATLAB can read?

    cursor=stop_id
    subclip_ct+=1

print('Done exporting Files')