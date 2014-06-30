#Script to copy (and possibly inspect the metadata) ConDep files from the
#receiver to a folder for import

import os
from operator import itemgetter, attrgetter
import cdpwavefile
import logging
import logging.handlers
import time

#Build a list of filenames in the receiver
srcFolder = "\\\\cdproaudio2\\xdcache\\CDCutId\\"
destFolder = "\\CDautoload\\"
logFileName = "synclog.txt"

RXfiles = [] #os.listdir(srcFolder)
transfer_times = []
CdpFile = cdpwavefile.CDPFile()

for file in os.listdir(srcFolder):
    RXfiles.append([file, os.path.getsize(srcFolder + file), tuple(os.stat(srcFolder + file))[7:9]])
RXfiles = sorted(RXfiles, key=itemgetter(1), reverse=False)
#print RXfiles

#Set up logging
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
	logFileName, maxBytes=100000, backupCount=5)
formatter = logging.Formatter("**%(asctime)s - %(levelname)s--> %(message)s")
handler.setFormatter(formatter)
my_logger.addHandler(handler)

my_logger.info('Starting script')
#print RXfiles

for name, size, times in RXfiles:
    data = '0'
    x = open(srcFolder + name, 'rb', 8192)
    my_logger.debug('Opening source file ' + srcFolder + name)
    y = open(destFolder + name + ".part", 'wb')
    my_logger.debug('Opening dest file ' + destFolder + name)
    start_time = time.clock()
    data = x.read(524288)
    CdpFile.SearchWaveDataBlob(data)
    my_logger.info(CdpFile.cart)
    my_logger.info(CdpFile.fact)
    while data != '':
	y.write(data)
	#time.sleep(0.1)
	elapsed_time = time.clock() - start_time
	transfer_times.append((elapsed_time, len(data)))
	start_time = time.clock()
	data = x.read(524288)
    x.close()
    y.close()
    my_logger.debug('Done copying ' + destFolder + name)
    if os.path.isfile(destFolder + name):
	my_logger.warn("Overwriting file " + destFolder + name)
	os.remove(destFolder + name)
    os.rename(destFolder + name + ".part",
	      destFolder + name )
    os.utime(destFolder + name, times)
    os.unlink(srcFolder + name)
    my_logger.info('Copied {0:1.1f} KB file'.format(os.stat(
                      destFolder + name).st_size / 1024))

#print transfer_times
avg_transfer_rate = 0
for datapoints in transfer_times:
    avg_transfer_rate = (avg_transfer_rate + (datapoints[1] / datapoints[0]) ) / 2

#print avg_transfer_rate / 1024
if len( transfer_times ) > 0:
    my_logger.info('Avg transfer rate: {0:1.3f} KB/s'.format(avg_transfer_rate / 1024))

my_logger.info('End of script')
