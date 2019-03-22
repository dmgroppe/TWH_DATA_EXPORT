""" This function takes a lay file (Persyst data file), removes bad channels, converts to avg ref, and saves
the data to disk in max-1 hour clips. Annotations are also saved. Note, a szr class time series is added to each clip
by another script, AddSzrClass2Npz.py"""

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
# TODO maybe just have filename as input and grab patient_id?
if len(sys.argv)==1:
    print('Usage: lay2npz.py lay_file_and_path patient_id out_dir (e.g., ../blah.lay TWH081)')
    exit()
if len(sys.argv)!=4:
    raise Exception('Error: lay2npz.py requires 3 arguments: lay_file_and_path patient_id out_dir')

# Import Parameters from command line
lay_fname=sys.argv[1]
#  subnum=sys.argv[2]
patient_id=sys.argv[2]
out_dir=sys.argv[3]

# Get first chunk of random part of filename to help identify clips from the same file
lay_fname_code_prefix=lay_fname.split('_')[-1].split('-')[0]
just_lay_fname=lay_fname.split('/')[-1]

# Load file
debug=False
if debug: #TODO undo debugging
    print('*********************** IN DEBUGGING MODE ***********************')
    [hdr, ieeg] = lr.layread(lay_fname, importDat=True, timeLength=3600 * 1000 + 60 * 1000)
    # [hdr, ieeg]=lr.layread(lay_fname,importDat=False) # TODO undo false, just using false for developing
    # ieeg=np.zeros((125,1000))
else:
    [hdr, ieeg]=lr.layread(lay_fname,importDat=True)
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

# Remove artifactual channels TODO replace this with p(bad) derived from a subsequent script
#ieeg, clip_hdr['channel_names']=rm_bad_chans(clip_hdr['patient_id'],ieeg,clip_hdr['channel_names'])

# Prune annotations
clip_hdr['annotations']=lr.prune_annotations(hdr['annotations'])

# Get list of sample ids in the entire continuous file
annot_tpts=[]
for annot in clip_hdr['annotations']:
    annot_tpts.append(annot['sample'])

# Get time in seconds corresponding to each time point
time_of_day_sec=lr.sample_times_sec(hdr['rawheader']['sampletimes'],n_tpt,1/hdr['samplingrate'])
print(len(time_of_day_sec))
print(time_of_day_sec[:5])

# Get day of recording relative to first date of electrode implantation
subnum=patient_id[3:]
implant_day_str=getImplantDate(subnum) #TODO see if I can just use patient_id
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

# Limit time_of_day_sec range to 0-24*3600
time_of_day_sec=time_of_day_sec%(24*3600)

# Have a separate output directory for each patient
out_path=os.path.join(out_dir,clip_hdr['patient_id'])
if os.path.isdir(out_path)==False:
    os.makedirs(out_path)

# Load/create dataframe of annotations: annotation/szr onset/offset, time since implant in sec,
# clip filename, tpt in clip
annotFname=patient_id+'_annot.tsv'
annotFnameFull=os.path.join(out_path,annotFname)
if os.path.isfile(annotFnameFull):
    annot_df=pd.read_csv(annotFnameFull,sep='\t')
else:
    # create annotation dataframe
    # Note, I don't know what units Duration is in sinceI think it is 0 in all the annotations I've seen
    colNames = ['Annotation', 'SecondsSinceImplant', 'Duration', 'ClipFilename', 'ClipTpt']
    annot_df = pd.DataFrame(columns=colNames)

# Save data in 1 hour clips
cursor=0
n_tpt_per_hour=clip_hdr['srate_hz']*3600
subclip_ct=0
while cursor<n_tpt:
    # Save header dict via pickle; If you want to do this, you need to remove year from clip_hdr annotations
    # if subclip_ct==0:
    #     hdr_fname=clip_hdr['patient_id'] +'_'+lay_fname_code_prefix+'_hdr.pkl'
    #     pickle.dump(clip_hdr, open(os.path.join(out_path,hdr_fname), 'wb'))

    print('Working on subclip %d' % subclip_ct)
    stop_id=np.min([n_tpt, cursor+n_tpt_per_hour])
    print('{} {}'.format(cursor,stop_id))

    ieeg_fname = clip_hdr['patient_id'] + '_'+str(np.int(seconds_since_implant[cursor]))+'-'+lay_fname_code_prefix+'-'+str(subclip_ct)
    print('Saving clip %s' % ieeg_fname)

    # Get the list of annotations that fall within the current clip
    in_clip_id = []
    for ct, annot_sample in enumerate(annot_tpts):
        if (annot_sample >= cursor) and (annot_sample < stop_id):
            in_clip_id.append(ct)
    # Add annotations to data frame
    for indx in in_clip_id:
        tempDict = {}
        tempDict['Annotation'] = [clip_hdr['annotations'][indx]['text']]
        tempDict['SecondsSinceImplant'] = [seconds_since_implant[clip_hdr['annotations'][indx]['sample']]]
        tempDict['ClipFilename'] = [ieeg_fname]
        tempDict['ClipTpt'] = [clip_hdr['annotations'][indx]['sample'] - cursor]
        tempDict['Duration'] = [clip_hdr['annotations'][indx]['duration']]
        tempDf = pd.DataFrame(data=tempDict)
        # annot_df.append(tempDict)
        annot_df = annot_df.append(tempDf, sort=False)

    # Save numeric data in NPZ format
    np.savez(os.path.join(out_path,ieeg_fname),
            ieeg=ieeg[:,cursor:stop_id],
            chan_names=clip_hdr['channel_names'],
            patient_id=patient_id,
            time_of_day_sec=time_of_day_sec[cursor:stop_id],
            seconds_since_implant=seconds_since_implant[cursor:stop_id],
            srate_hz=clip_hdr['srate_hz'],
            lay_fname=just_lay_fname,
            days_since_implant=days_since_implant)

    # Save numeric data in MATLAB format
    # mat_dict=dict()
    # mat_dict['ieeg']=ieeg[:, cursor:stop_id]
    # mat_dict['ieeg_mn']=ieeg_mn[cursor:stop_id]
    # mat_dict['szr_class']=szr_class[cursor:stop_id]
    # mat_dict['time_of_day_sec']=time_of_day_sec[cursor:stop_id]
    # mat_dict['srate_hz']=clip_hdr['srate_hz']
    # sio.savemat(os.path.join(out_path,ieeg_fname), mat_dict)

    cursor=stop_id
    subclip_ct+=1

print('Saving dataframe of annotations to %s' % annotFname)
annot_df.drop_duplicates(inplace=True)
annot_df.to_csv(annotFnameFull,sep='\t',index=False)


print('Done exporting files')