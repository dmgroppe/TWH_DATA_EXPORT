
# This script finds all the patient directories in rootDir and then finds all the dat files
# in each directory and then it compresses them.

import os
import sys

subs=list()
rootDir = '/media/dgroppe/Seagate Expansion Drive/PersystFormat/'
# for f in os.listdir(rootDir):
#     if f.startswith('TWH') and os.path.isdir(os.path.join(rootDir,f)):
#         #print(f)
#         subs.append(f)
# subs.sort()
# print('Found the following directories of patient data:')
# print(subs)


if len(sys.argv)==1:
    print('Usage: UncompressDatFiles.py subnum (e.g., UncompressDatFiles.py TWH081)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: UncompressDatFiles.py requires 1 argument: subnum')

patientId=sys.argv[1]

#exit()
# subs=['TWH076']

# for patientId in subs:
print('Compressing data from %s' % patientId)
# Find all dat files
#patientId='TWH071'
#patientId='TWH082'
patientDir=os.path.join(rootDir,patientId)
datFnames=list()
for f in os.listdir(patientDir):
    if f.endswith('.bz2'):
        datFnames.append(f)
        print(f)
print('%d bz2 files found for %s' % (len(datFnames),patientId))

# Uncompress all dat files
for f in datFnames:
    cmnd="bzip2 -d '"+os.path.join(patientDir,f)+"' "
    #cmnd="ls '"+os.path.join(patientDir,f)+"' "
    print("Running: %s" % cmnd)
    returnedVal=os.system(cmnd)
    print('returned value:', returnedVal)
print('Done with %s!!!' % patientId)
print('***** ALL Done! *****')

