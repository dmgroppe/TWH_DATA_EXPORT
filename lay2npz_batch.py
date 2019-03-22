# Script for running lay2npz.py on all lay files in a directory
import os
import sys

if len(sys.argv)==1:
    print('Usage: lay2npz_batch.py patient_id (e.g., TWH001)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: lay2npz_batch.py requires 1 argument: patient_id')

patientId=sys.argv[1]

if True:
    inDir=os.path.join("/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/DATA_SBOX/",patientId)
    outDir=os.path.join("/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PY_DATA",patientId)
else:
    inDir=os.path.join("/media/dgroppe/Seagate Expansion Drive/PersystFormat/",patientId)
    outDir=os.path.join("/media/dgroppe/ValianteLabEuData/PY_DATA/",patientId)
#Usage: lay2npz.py lay_file_and_path patient_id out_dir (e.g., ../TWH001/blah.lay TWH001 ../PY_DATA/TWH001)
for f in os.listdir(inDir):
    if f.endswith('.lay'):
        cmnd="python lay2npz.py '"+os.path.join(inDir,f)+"' "+patientId+" '"+outDir+"'"
        print(cmnd)
        #os.system(cmnd)