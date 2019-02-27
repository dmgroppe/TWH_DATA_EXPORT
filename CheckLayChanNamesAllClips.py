
# coding: utf-8

# This code reads the channel names from a lay files to see make sure the names are all the same

# In[2]:


import numpy as np
import pandas as pd
import os 
import layread as lr


# In[ ]:


def checkUnique(nameList):
    allUnique=True
    if len(nameList)==len(np.unique(nameList)):
        print("All channels have unique names.")
    else:
        allUnique=False
        raise Exception('Two or more channels have the exact same name.')


# In[29]:


root_dir="/Volumes/Seagate Expansion Drive/PersystFormat/TWH081"
lay_fnames=list()
for f in os.listdir(root_dir):
    if f.endswith('.lay'):
        lay_fnames.append(f)
print('%d lay files found' % len(lay_fnames))


# In[30]:


print(lay_fnames[1])


# In[41]:


# Get channel names from first file
[eegHdr, eegData]=lr.layread(os.path.join(root_dir,lay_fnames[0]),importDat=False)
layChanMap=eegHdr['rawheader']['channelmap']

# TODO make sure channel names are unique

# Loop over remaining lay files to see if channel names are compatible
altChanMaps=list()
altChanMapFname=list()
for f in lay_fnames[1:]:
#for f in lay_fnames[1:2]:
    [eegHdr, eegData]=lr.layread(os.path.join(root_dir,f),importDat=False)
    tempLayChanMap=eegHdr['rawheader']['channelmap']
    if tempLayChanMap!=layChanMap:
        print('Channel names in file %s NOT the Same!' % f)
        altChanMaps.append(tempLayChanMap.copy())
        altChanMapFname.append(f)
        if len(tempLayChanMap)==len(layChanMap):
            print('They have the same # of chans')
        else:
            print('They do NOT have the same # of chans')
    else:
        print('Same!')


# In[44]:


for id in range(len(altChanMaps)):
    print('AltMap file #%d %s' % (id,altChanMapFname[id]))
    print('FirstLayFile\tAltMap')
    for a in range(len(layChanMap)):
        print('%s\t%s' % (layChanMap[a],altChanMaps[id][a]))
    print()


# In[ ]:


# Ask user if mismatched channel names should be moved to a new directory
#TODO

