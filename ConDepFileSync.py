#Script to copy (and possibly inspect the metadata) ConDep files from the
#receiver to a folder for import

import os
from operator import itemgetter, attrgetter
import cdpwavefile
import logging
import logging.handlers
import time

#Build a list of filenames in the receiver
#RXfiles = os.listdir(r"\\cdfile1\xdcache\CDCutId")
srcFolder = "\\ConDep\\cdfile1\\xdcache\\CDCutId\\"
destFolder = "\\ConDep\\aserv3\\CDautoload\\"
logFileName = "synclog.txt"

RXfiles = [] #os.listdir(srcFolder)
transfer_times = []
CdpFile = cdpwavefile.CDPFile()

for file in os.listdir(srcFolder):
    RXfiles.append([file, os.path.getsize(srcFolder + file)])
RXfiles = sorted(RXfiles, key=itemgetter(1), reverse=False)
print RXfiles

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

for file in RXfiles:
    data = '0'
    x = open(srcFolder + file[0], 'rb', 8192)
    my_logger.debug('Opening source file ' + srcFolder + file[0])
    y = open(destFolder + file[0] + ".part", 'wb')
    my_logger.debug('Opening dest file ' + destFolder + file[0])
    start_time = time.clock()
    data = x.read(524288)
    CdpFile.SearchWaveDataBlob(data)
    my_logger.info(CdpFile.cart)
    while data != '':
	y.write(data)
	#time.sleep(0.1)
	elapsed_time = time.clock() - start_time
	transfer_times.append((elapsed_time, len(data)))
	start_time = time.clock()
	data = x.read(524288)
    x.close()
    y.close()
    my_logger.debug('Done copying ' + destFolder + file[0])
    if os.path.isfile(destFolder + file[0]):
	my_logger.warn("Overwriting file " + destFolder + file[0])
	os.remove(destFolder + file[0])
    os.rename(destFolder + file[0] + ".part",
	      destFolder + file[0] )
    #os.unlink(srcFolder + file[0])

#print transfer_times
avg_transfer_rate = 0
for transfer_time, num_bytes in transfer_times:
    avg_transfer_rate = (avg_transfer_rate + (num_bytes / transfer_time) ) / 2

#print avg_transfer_rate / 1024
if len( transfer_times ) > 0:
    my_logger.info('Avg transfer rate: {0:1.3f} KB/s'.format(avg_transfer_rate / 1024 ))

my_logger.info('End of script')

