""" This function simply exports a sub-spreadsheet of one subject from Victoria's master spreadsheet"""
import pandas as pd
import numpy as np
import os
import sys


### START OF MAIN FUNCTION ###
if len(sys.argv)==1:
    print('Usage: Xls2Tsv.py subnum (e.g., Xls2Tsv.py 081)')
    exit()
if len(sys.argv)!=2:
    raise Exception('Error: lay2npz.py requires 1 argument: subnum')

sub=sys.argv[1]

xlsFname='PRIVATE/ANON_SeizureCounts_20181004.xlsx'
# df=pd.read_excel(xlsFname)
xl = pd.ExcelFile(xlsFname)
print("THESE ARE ALL THE SUBSHEETS IN VICTORIA'S MASTER XLS FILE:")
print(xl.sheet_names)

df = xl.parse('TWH_'+sub)
print("First 4 rows for %s" % sub)
print(df.head())

# Double check that all the columns we need are there
dfColNames=list(df.columns.values)
# Convert to lowercase
for ct, colName in enumerate(dfColNames):
    dfColNames[ct]=colName.lower()
df.columns=dfColNames
neededCols=['actual date','start time', 'end time','class'] # all need to be lowercase
for col in neededCols:
    if col.lower() not in dfColNames:
        print('ERROR: This spreadsheet is missing a column named %s' % col)
        print('Exiting.')
        exit()

outfile=os.path.join('PRIVATE/SZR_TIMES','TWH'+sub+'_SzrOnset.tsv')
print('Exporting spreadsheet as %s' % outfile)
df.to_csv(outfile,sep='\t',index=False)

