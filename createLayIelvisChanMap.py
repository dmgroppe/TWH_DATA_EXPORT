""" TODO ADD COMMENTS """
import pandas as pd
import os
import sys
import numpy as np

###### Start of main function
if len(sys.argv)==1:
    print('Usage: createLayIelvisChanMap.py sub_id (e.g., createLayIelvisChanMap.py TWH018)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: createLayIelvisChanMap.py requires 1 argument: sub_id')

sub = sys.argv[1]

# Get mapping between iELVis and Lay electrode name stems
chanMapDir='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/LAY2IELVIS_MAPS'
stemMapFnameFull=os.path.join(chanMapDir,sub+'_stemMapping.tsv')
if not os.path.isfile(stemMapFnameFull):
    print("Error: missing file %s" % stemMapFnameFull)
    exit()
stemDf=pd.read_csv(stemMapFnameFull,sep='\t', header=0)
print('Stem Mapping:')
print(stemDf.head())

# Get list of iELVis electrode names (with contact #s)
fsDir=os.environ['SUBJECTS_DIR']
elecReconDir=os.path.join(fsDir,sub,'elec_recon')
ielvisLabelFname=sub+'.stemAndNumber'
ielvisLabelFnameFull=os.path.join(elecReconDir,ielvisLabelFname)
if not os.path.isfile(ielvisLabelFnameFull):
    print("Error: missing file %s" % ielvisLabelFnameFull)
    exit()
ielvisDf=pd.read_csv(ielvisLabelFnameFull,sep='\t', header=0)
print('iELVis Labels:')
print(ielvisDf.head())

# Create dict to map from iELVis to Lay stems
nStem=stemDf.shape[0]
stemDict=dict()
for ct in range(nStem):
    stemDict[stemDf['iELVisStem'][ct]]=stemDf['LayStem'][ct]

lay2ielvisFname=os.path.join(chanMapDir,sub+"_lay2ielvis.tsv")
print('Writing lay to iELVis channel mapping as %s' % lay2ielvisFname)
# ielvisStems=list(stemDf['iELVisStem'])
# layStems=list(stemDf['LayStem'])
# nStemElec=list(stemDf['nContacts'])
nElec=ielvisDf.shape[0]



sys.stdout = open(lay2ielvisFname,'wt')
print('iELVisChanName\tlayChanName')
for ct in range(nElec):
    ielName=ielvisDf['Stem'][ct]+np.array2string(ielvisDf['Number'][ct])
    layName=stemDict[ielvisDf['Stem'][ct]]+np.array2string(ielvisDf['Number'][ct])
    print('%s\t%s' % (ielName, layName))
# for ct, iStem in enumerate(ielvisStems):
#     for elecCt in range(nStemElec[ct]):
#         print('%s%d\t%s%d' % (iStem, elecCt + 1, layStems[ct], elecCt + 1))

