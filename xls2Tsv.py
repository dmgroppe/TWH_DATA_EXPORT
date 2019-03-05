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

xlsFname='/Users/davidgroppe/PycharmProjects/TWH_DATA_EXPORT/PRIVATE/ANON_SeizureCounts_20181004.xlsx'
# df=pd.read_excel(xlsFname)
xl = pd.ExcelFile(xlsFname)
print("THESE ARE ALL THE SUBSHEETS IN VICTORIA'S MASTER XLS FILE:")
print(xl.sheet_names)

df = xl.parse('TWH_'+sub)
print("First 4 rows for %s" % sub)
print(df.head())

print('a\tb')

outfile=os.path.join('PRIVATE/SZR_TIMES','TWH'+sub+'_SzrOnset.tsv')
print('Exporting spreadsheet as %s' % outfile)
df.to_csv(outfile,sep='\t',index=False)

