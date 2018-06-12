"""
Simple script for creating a strat plot of EEG data stored in temp.npz (needs to be in a variable called ieeg)
"""
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

npz=np.load('temp.npz')
ieeg=npz['ieeg']
print(ieeg.shape)
n_chan, n_tpt=ieeg.shape

#conver to avg ref:
for t in range(n_tpt):
    ieeg[:,t]-=np.mean(ieeg[:,t])

offset=500
for c in range(n_chan):
    ieeg[c,:]=ieeg[c,:]+offset*c

plt.figure(1)
plt.clf()
plt.plot(ieeg.T)
plt.show()


