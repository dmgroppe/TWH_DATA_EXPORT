import numpy as np
import os
import pandas as pd
import layread as lr
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import scipy.signal as sig
import re
import pickle
from datetime import datetime

##### USEFUL FUNCTIONS #####
def rm_bad_chans(patient_id,ieeg,chan_names):
    # Load names of artifact ridden channels from text file
    # If the channel names ends in "?", that means it may have usable data
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


def get_szr_bool(annot, n_tpt):
    # Note, I assume that annotations in annot ordered from earliest to latest occurrence
    # TODO: double check
    szr_bool = np.zeros(n_tpt, dtype=bool)  # default=no seizures
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
            szr_bool = szr_bool + True
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
                szr_bool[a['sample']:] = True
            elif annot_text[ct] in offset_text:
                # Szr offset
                szr_bool[a['sample']:] = False
    else:
        print('No szrs found in these data')
    return szr_bool



## THIS IS THE WHOLE WORKFLOW ##
## Start of main function
# TODO read path to files from command line
# if len(sys.argv)==1:
#     print('Usage: train_smart_srch_multi_patient.py srch_params.json')
#     exit()
# if len(sys.argv)!=2:
#     raise Exception('Error: train_smart_srch_multi_patient.py requires 1 argument: srch_params.json')
#
# # Import Parameters from json file
# param_fname=sys.argv[1]
# print('Importing model parameters from %s' % param_fname)
# with open(param_fname) as param_file:
#     params=json.load(param_file)
# model_name=params['model_name']


# Load file
#lay_fname='/media/dgroppe/ValianteLabEuData/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
#lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'
# short clip for code testing
#lay_fname='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/DATA_SBOX/TWH018_2402fec8-303e-4afe-b398-725f90dcffb7_clip.lay'

# 1 day clip with 3 szrs
lay_fname='/Users/davidgroppe/ONGOING/PERSYST_DATA_LONG/TWH056/TWH056_ShGa_dbf43bc5-601b-4e71-9b2d-175ea763242f-archive.lay'

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

# TODO Set szr_bool
#szr_bool=np.zeros(n_tpt, dtype=bool)
szr_bool=get_szr_bool(clip_hdr['annotations'],n_tpt)

# Save data in 1 hour clips
clip_ct=0 # TODO, retrieve this from CSV?
cursor=0
n_tpt_per_hour=clip_hdr['srate_hz']*3600
subclip_ct=0
while cursor<n_tpt:
    print('Working on subclip %d' % subclip_ct)
    stop_id=np.min([n_tpt, cursor+n_tpt_per_hour])
    print('{} {}'.format(cursor,stop_id))
    ieeg_fname_npz=clip_hdr['patient_id']+'_Day-'+str(day_since_implant)+'_Clip-'+str(clip_ct)+'-'+str(subclip_ct)
    print('Saving clip %s' % ieeg_fname_npz)
    np.savez(ieeg_fname_npz,
            ieeg=ieeg[:,cursor:stop_id],
            ieeg_mn=ieeg_mn[cursor:stop_id],
            szr_bool=szr_bool[cursor:stop_id],
            time_of_day_sec=time_of_day_sec[cursor:stop_id],
            srate_hz=clip_hdr['srate_hz'],
            day_since_implant=day_since_implant)
    if subclip_ct==0:
        hdr_fname = clip_hdr['patient_id'] + '_Day-' + str(day_since_implant) + '_Clip-' + str(clip_ct)+'_hdr.pkl'
        pickle.dump(clip_hdr, open(hdr_fname, 'wb'))
    cursor=stop_id
    subclip_ct+=1

print('Done exporting Files')