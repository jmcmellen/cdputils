#!/bin/python
#===============================================================
#  makecondep.py - A utility to wrap an MP2 audio file with
#  RIFF WAVE chunks using CartChunk and BWF chunks, generating
#  a WAVE file similar to those used by ContentDepot(TM)
#  Uses the cdpfile.py library functions
#  February 4, 2010
#
#===============================================================
#
#===============================================================
#License (see the MIT License)
#
#Copyright (c) 2009 John McMellen
#
#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
#
#=================================================================

#PYTHON 2.6 REQUIRED

from cdpwavefile import *
from optparse import OptionParser
import sys

program_version = "1.3"

parser = OptionParser(usage="usage: %prog [options] PCM/MP2inputfile wrappedoutputfile")
parser.add_option("-v", "--ver", dest="show_version",
	action="store_true", default=False,
	help="show program version")
parser.add_option("-t", "--title", dest="title", 
	help="set CartChunk Title to TITLE")
parser.add_option("-a", "--artist", dest="artist", 
	help="set CartChunk Artist to ARTIST")
parser.add_option("-c", "--cutnum", dest="cutnum", 
	help="set CartChunk Cutnum to CUTNUM")
parser.add_option("-q", "--outcue", dest="outcue", 
	help="set CartChunk Outcue to OUTCUE")
parser.add_option("--startdate", dest="startdate", 
	help="set CartChunk StartDate to YYYY/MM/DD")
parser.add_option("--starttime", dest="starttime", 
	help="set CartChunk StartTime to 24 hour HH:MM:SS")
parser.add_option("--enddate", dest="enddate",
	help="set CartChunk EndDate to YYYY/MM/DD")
parser.add_option("--endtime", dest="endtime",
	help="set CartChunk EndTime to 24 hour HH:MM:SS")
parser.add_option("--appid", dest="appid", default="PythonUtil",
	help="set CartChunk AppID to APPID, default value is PythonUtil")
parser.add_option("--appver", dest="appver", default=program_version,
	help="set CartChunk AppVersion to APPVER, default value is" \
	" {0}".format(program_version))
parser.add_option("--url", dest="url",
	help="set CartChunk URL field to URL")
parser.add_option("--tagtext-in", dest="tagtextinfile", 
	help="import TagText value from FILE", metavar="FILE")
parser.add_option("--restore-cart", dest="cart_xml_filename",
	help="restore cart chunk info (minus TagText) from FILE",
	metavar="FILE")
(options, args) = parser.parse_args()

def main():
    if options.show_version:
	print "Makecondep Version {0}/Core version {1}".format(program_version,
		cdpwavefile_core_version)
	if len(args) != 2:
	    sys.exit()
    if len(args) != 2:
	parser.error("Input or output file not specified. " 
		"Try {0} -h for detailed help."
		.format(os.path.basename(sys.argv[0])))
    inputfile = args[0]
    outputfile = args[1]
    MyCDPFile = CDPFile()
    MyCDPFile.cart.tagtext = ""
    try:
	if re.match(r'.*\.mp2$', inputfile, re.I) is not None:
	    MyCDPFile.ImportMpegFile(inputfile)
	elif re.match(r'.*\.wav$', inputfile, re.I) is not None:
	    MyCDPFile.ReadWaveFile(inputfile)
	else:
	    raise Exception("Unrecognized filename extension on file: {0}".format(
		inputfile))
	if options.cart_xml_filename is not None:
	    with open(options.cart_xml_filename, 'r') as x:
		print "Restoring CartChunk values from {0}".format(
			options.cart_xml_filename)
		MyCDPFile.cart.ImportXMLValues(x.read())
		options.appid = None
		options.appver = None
	for option, value in options.__dict__.iteritems():
	    if value is not None:
		try:
		    getattr(MyCDPFile.cart, option)
		    setattr(MyCDPFile.cart, option, value)
		    print "Setting '{0}' to '{1}'".format(option, value)
		except AttributeError:
		    pass
	if options.tagtextinfile is not None:
	    with open(options.tagtextinfile, 'r') as f:
		print "Imported TagText from {0}".format(options.tagtextinfile)
		MyCDPFile.cart.tagtext = f.read()
	#print MyCDPFile
	if MyCDPFile.fmt.compressioncode == 80:
	    MyCDPFile.WriteCompressedWaveFile(outputfile)
	elif MyCDPFile.fmt.compressioncode == 1:
	    MyCDPFile.WritePCMWaveFile(outputfile)	
	else:
	    raise Exception("Incompatible input file type: {0}".format(
		inputfile))
    except InvalidMPEGDataError as inst:
	print "There was a problem with the MPEG data. " \
	      "Are you sure it is a valid MP2 audio file with no ID3 tags?"
	print "Error: {0}".format(inst)
    except IOError as inst:
	print "An IO error occurred"
	print inst
    except ValueError as inst:
	print "Unable to set an attribute value. " \
	      "Are you sure you entered dates and times in the right format?"
	print "Error: {0}".format(inst)
    except Exception as inst:
	print "An undefined error occurred"
	print type(inst)
	print inst.args
	print inst

if __name__ == "__main__":
    main()

