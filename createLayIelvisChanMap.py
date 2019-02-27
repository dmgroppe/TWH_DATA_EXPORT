import pandas as pd
import os
import sys

###### Start of main function
if len(sys.argv)==1:
    print('Usage: createLayIelvisChanMap.py sub_id (e.g., createLayIelvisChanMap.py TWH018)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: createLayIelvisChanMap.py requires 1 argument: sub_id')

sub = sys.argv[1]

chanMapDir='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/LAY2IELVIS_MAPS'
stemMapFname=os.path.join(chanMapDir,sub+'_stem_mapping.tsv')
stemDf=pd.read_csv(stemMapFname,sep='\t', header=0)
print('Stem Mapping:')
print(stemDf.head())

lay2ielvisFname=os.path.join(chanMapDir,sub+"_lay2ielvis.tsv")
print('Writing lay to iELVis channel mapping as %s' % lay2ielvisFname)
ielvisStems=list(stemDf['iELVisStem'])
layStems=list(stemDf['LayStem'])
nStemElec=list(stemDf['nContacts'])
f=open(lay2ielvisFname,'w')
print('iELVisChanName\tlayChanName',file=f)
for ct, iStem in enumerate(ielvisStems):
    for elecCt in range(nStemElec[ct]):
        print('%s%d\t%s%d' % (iStem,elecCt+1,layStems[ct],elecCt+1),file=f)
f.close()