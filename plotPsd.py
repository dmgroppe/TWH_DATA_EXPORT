import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import layread as lr
import os
import matplotlib.pyplot as plt
#from sklearn import preprocessing
from scipy import signal

def on_pick(event):
    artist = event.artist
    xmouse, ymouse = event.mouseevent.xdata, event.mouseevent.ydata
    x, y = artist.get_xdata(), artist.get_ydata()
    ind = event.ind
    print('Artist picked:', event.artist)
    print('{} vertices picked'.format(len(ind)))
    print('Pick between vertices {} and {}'.format(min(ind), max(ind)+1))
    print('x, y of mouse: {:.2f},{:.2f}'.format(xmouse, ymouse))
    print('Data point:', x[ind[0]], y[ind[0]])
    print()

# Get list of lay files
sub='TWH076'
fileRoot='/media/dgroppe/Seagate Expansion Drive/PersystFormat/'+sub
layFnames=list()
for f in os.listdir(fileRoot):
    if f.endswith('.lay'):
        layFnames.append(f)

nFiles=len(layFnames)
print('%d lay files found' % nFiles)

# Read in random samples of each lay file & compute PSD
offset = 100000
nTpt = 1024 * 1000
for f in layFnames[0:1]:  # TODO make this go over all files
    print('Reading data from %s' % f)
    # Get the time point index of the last time stamp. This is an underestimate of how many time points are in the file

    [hdr, ieeg] = lr.layread(os.path.join(fileRoot, f), timeOffset=offset,
                             timeLength=nTpt)  # Make offset random based on # of time points in the file
    print('Sampling rate is: %f' % hdr['samplingrate'])

# Compute PSD
srateHz=hdr['samplingrate']
#freqs, psd = signal.welch(ieeg[0:3,:],fs=srateHz,nperseg=srateHz*2)
freqs, psd = signal.welch(ieeg,fs=srateHz,nperseg=srateHz*2)

fig, ax = plt.subplots()
tolerance = 10
#ax.plot(freqs, 10*np.log10(psd.T))
for a in range(psd.shape[0]):
    ax.plot(freqs, 10*np.log10(psd[a,:]))

# plt.title('PSD: power spectral density')
# plt.xlabel('Frequency')
# plt.ylabel('Power')
# plt.tight_layout()
# plt.figure(figsize=(5, 4))
# for a in range(psd.shape[0]):
#     plt.semilogy(freqs, psd[a,:])
# plt.title('PSD: power spectral density')
# plt.xlabel('Frequency')
# plt.ylabel('Power')
# plt.tight_layout()

# fig, ax = plt.subplots()
#
# tolerance = 10 # points
# #ax.plot(range(10), 'ro-', picker=tolerance)
# ax.plot(np.random.randn(10), 'ro-', picker=tolerance)
#
# fig.canvas.callbacks.connect('pick_event', on_pick)

plt.show()
