
# This script finds all the patient directories in rootDir and then finds all the dat files
# in each directory and then it compresses them.


import os

subs=list()
rootDir = '/media/dgroppe/Seagate Expansion Drive/PersystFormat/'
for f in os.listdir(rootDir):
    if f.startswith('TWH') and os.path.isdir(os.path.join(rootDir,f)):
        #print(f)
        subs.append(f)
subs.sort()
print('Found the following directories of patient data:')
print(subs)

print("Removing TWH066 as I'm working with that data.")
subs.remove('TWH066')
print(subs)

#exit()
#subs=['TWH071','TWH082']

for patientId in subs:
    print('Compressing data from %s' % patientId)
    # Find all dat files
    #patientId='TWH071'
    #patientId='TWH082'
    patientDir=os.path.join(rootDir,patientId)
    datFnames=list()
    for f in os.listdir(patientDir):
        if f.endswith('.dat'):
            datFnames.append(f)
            print(f)
    print('%d dat files found for %s' % (len(datFnames),patientId))

    # Compress all lay files
    for f in datFnames:
        cmnd="bzip2 -f '"+os.path.join(patientDir,f)+"' "
        #cmnd="ls '"+os.path.join(patientDir,f)+"' "
        print("Running: %s" % cmnd)
        returnedVal=os.system(cmnd)
        print('returned value:', returnedVal)
    print('Done with %s!!!' % patientId)
print('***** ALL Done! *****')

