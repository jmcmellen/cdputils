#!/usr/bin/python

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

from struct import *
from xml.dom.minidom import parse, parseString, getDOMImplementation
import re
import os.path

cdpwavefile_core_version = 1.6

class InvalidMPEGDataError(Exception):
    """A custom exception to indicate any problems decoding MPEG data fields in the header or possibly conflicting settings"""
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)

class CartChunk:
    """A Class representing the fields in a CartChunk chunk"""
    formatstring = "<4s64s64s64s64s64s64s64s10s8s10s8s64s64s64sL64s276s1024s{0}s"
    #formatstring = "<4s64s64s64s64s64s64s64s10s8s10s8s64s64s64sH340s716s{0}s"
    #formatstring = "<4s64s64s64s64s64s64s64s10s8s10s8s64s64s64sH32s1024s{0}s"
    def __init__(self):
	self.xmlfields = ["version", "title", "artist", "cutnum", "clientid", 
	    "category", "classification", "outcue", "startdate", "starttime",
	    "enddate", "endtime", "appid", "appver", "userdef", "zerodbref",
	    "posttimers", "url"]
        self.version = "0101"
        self.title = ""
        self.artist = ""
        self.cutnum = ""
        self.clientid = ""
        self.category = ""
        self.classification = ""
        self.outcue = ""
        self.startdate = "2000/01/01"
        self.starttime = "00:00:00"
        self.enddate = "2030/12/31"
        self.endtime = "23:59:59"
        self.appid = "ContentDepot"
        self.appver = "1.0"
        self.userdef = ""
        self.zerodbref = 0
        self.posttimers = [("\x00" * 4, 0), ("\x00" * 4, 0), ("\x00" * 4, 0), 
		           ("\x00" * 4, 0), ("\x00" * 4, 0), ("\x00" * 4, 0),
		           ("\x00" * 4, 0), ("\x00" * 4, 0)]
	self.reserved = ""
        self.url = ""
        self.tagtext = '<program-associated-data><property' \
	     ' name="OwnerIdentifier" value="ContentDepot"/><property' \
	     ' name="Identifier" value="001"/><property name="Title"' \
	     ' value="Talk about ContentDepot"/><property name="Artist"' \
	     ' value="PRSS"/><property name="Album" value="ContentDepot' \
	     ' Test Program"/><property name="Genre" value="101"/><property' \
	     ' name="CommentTitle" value="This is a comment"/><property' \
	     ' name="Comment" value="These are test and placeholder fields' \
	     ' for ContentDepot PAD support in files. They are currently' \
	     ' generated from static fields in the ContentDepot Portal' \
	     ' database. Send email to prssplanning@npr.org if you have' \
	     ' questions."/></program-associated-data>'

    def __setattr__(self, attrname, value):
	if attrname == "enddate" or attrname == "startdate":
	    if re.match( r'[1-9][0-9][0-9][0-9]/[0-1][0-9]/[0-3][0-9]', value):
		self.__dict__[attrname] = value
	    else:
		self.__dict__[attrname] = value
		raise ValueError("Invalid date format provided for attribute"
			         " '{0}'. Should be YYYY/MM/DD".format(attrname))
	if attrname == "endtime" or attrname == "starttime":
	    if re.match( r'([0-2][0-3])|([0-1][0-9]):[0-5][0-9]:[0-5][0-9]', value):
		self.__dict__[attrname] = value
	    else:
		self.__dict__[attrname] = value
		raise ValueError("Invalid time format provided for attribute"
			         " '{0}'. Should be HH:MM:SS".format(attrname))
	if attrname == "zerodbref":
	    self.__dict__[attrname] = int(value)
	else:
	    self.__dict__[attrname] = value

    def __str__(self):
	if len(self.url) > 100:
	    url = self.url[:100] + "..."
	else:
	    url = self.url
	if len(self.tagtext) > 84:
	    tagtext = self.tagtext[:84] + "..."
	else:
	    tagtext = self.tagtext
	return """Version: {0}
Title: {1}
Artist: {2}
Cut Number: {3}
Client ID: {4}
Category: {5}
Classification: {6}
Out Cue: {7}
Start Time & Date: {8} {9}
End Time & Date: {10} {11}
Producer App ID: {12} 
Producer App Ver: {13}
User Defined field: {14}
Zero dB Reference: {15}
Post Timers: {16}
Reserved: {17}
URL: {18}
TagText: {19!r}
""".format(self.version, self.title, self.artist, self.cutnum, 
		self.clientid, self.category, self.classification, 
		self.outcue, self.starttime, self.startdate,
		self.endtime, self.enddate, self.appid, self.appver,
		self.userdef, self.zerodbref, self.posttimers, self.reserved,
		url, tagtext)

    def DecodeBinString(self, header, chunksize):
        #print self.formatstring
	#print chunksize
	data = zip( ("version", "title", "artist", "cutnum", "clientid", 
	    "category", "classification", "outcue", "startdate", "starttime",
	    "enddate", "endtime", "appid", "appver", "userdef", "zerodbref",
	    "posttimers","reserved", "url", "tagtext"), unpack(
		self.formatstring.format(len(header) - 2048), header))
	for objfield, value in data:
	    try:
		if objfield == "posttimers":
		    timerlist = []
		    for i in range(8):
			(postcode, sampleval) = unpack("<4sL", 
				value[i*8:(i*8)+8])
			timerlist.append((postcode, sampleval))
		    setattr(self, objfield, timerlist)
		else:
		    setattr(self, objfield, str(value).strip("\x00"))
	    except ValueError:
		pass
	    except Exception as inst:
		raise inst
	
    def EncodeBinString(self):
	posttimerstring = ""
	for (postcode, sampleval) in self.posttimers:
	    posttimerstring = posttimerstring + pack(
		                  "<4sL", postcode, sampleval)
	if len(posttimerstring) < 64:
	    posttimerstring = posttimerstring + "\x00" * (64 - len(
		posttimerstring))
	chunklen = 646	
	if len(self.tagtext) < chunklen:
	    tagtext = "\x00" * (646 - len(self.tagtext)) + self.tagtext
	else:
	    tagtext = self.tagtext
	    chunklen = len(self.tagtext)
	return pack(self.formatstring.format(len(self.tagtext)), self.version, 
		self.title, self.artist, self.cutnum, self.clientid, 
		self.category, self.classification, self.outcue, 
		self.startdate, self.starttime, self.enddate, self.endtime,
		self.appid, self.appver, self.userdef, self.zerodbref, 
		posttimerstring, self.reserved, self.url, self.tagtext)

    def ExportXMLValues(self):
	impl = getDOMImplementation()
	data = impl.createDocument(None, "cart", None)
	top_element = data.documentElement
	timerlist = []
	for postcode, sampleval in self.posttimers:
	    node = data.createElement("timer")
	    node.setAttributeNode(data.createAttribute("type"))
	    node.setAttribute("type", str(postcode).strip("\x00"))
	    node.appendChild(data.createTextNode(str(sampleval)))
	    timerlist.append(node)
	for field in self.xmlfields:
	    node = data.createElement(field)
	    if field == "posttimers":
		for timer in timerlist:
		    node.appendChild(timer)
	    else:
		node.appendChild(data.createTextNode(
		    str(getattr(self, field)) ))
	    top_element.appendChild(node)
	xmlstring = data.toxml()
	data.unlink()

	return xmlstring 

    def ImportXMLValues(self, xmlstring):
	#print xmlstring
	try:
	    data = parseString(xmlstring)
	    for field in self.xmlfields:
		if field == "posttimers":
		    node = data.getElementsByTagName(field)[0]
		    timerlist = []
		    for posttimer in node.childNodes:
			timerlist.append((str(posttimer.getAttribute("type")),
			    int(posttimer.firstChild.data)))
		    setattr(self, field, timerlist)
		else:
		    node = data.getElementsByTagName(field)[0].firstChild
		    if node is not None:
		   	 #print field, node.data
		        setattr(self, field, str(node.data))
		    else:
		        #print field
		        setattr(self, field, "")
	except ValueError as inst:
	    raise inst
	except IndexError as inst:
	    print "missing tags in xml - import failed:", field
	except Exception as inst:
	    print "invalid xml - import failed:", inst, field
	finally:
	    data.unlink()

class BextChunk:
    """Class that represents the fields in a EBU defined Bext Chunk"""
    formatstring = "<256s32s32s10s8sLLH64s190s{0}s"
    def __init__(self):
        self.title = ""
        self.author = ""
        self.reference = ""
        self.origindate = ""
        self.origintime = ""
        self.timereflow = 0
        self.timerefhigh = 0
        self.version = 1
        self.umid = "\x00" * 64
        self.reserved = ""
        self.codinghistory = "A=MPEG1L2,F=44100,B=256,M=STEREO,T=CV_PcxTl2NP\x0d\x0a"

    def __str__(self):
	return """Title: {0}
Author: {1}
Reference: {2}
Origination Date: {3}
Origination Time: {4}
Time Reference Low: {5}
Time Reference High: {6}
Version: {7}
SMTPE UMID: {8}
Reserved: {9}
Coding History: {10!r}
""".format( self.title, self.author, self.reference, self.origindate,
	    self.origintime, self.timereflow, self.timerefhigh, self.version,
	    "[unsupported]", self.reserved, self.codinghistory )

    def __setattr__(self, attrname, value):
	if (attrname == "timereflow" or
	    attrname == "timerefhigh" or
	    attrname == "version" ):
	    self.__dict__[attrname] = int(value)
	else:
	    self.__dict__[attrname] = value

    def DecodeBinString(self, header, chunksize):
	data = zip(("title", "author", "reference", "origindate", "origintime",
	    "timereflow", "timerefhigh", "version", "umid", "reserved", 
	    "codinghistory"), 
	    unpack(self.formatstring.format(len(header) - 602 ), header))
	for objfield, value in data:
	    try:
		setattr(self, objfield, str(value).strip("\x00"))
	    except Exception as inst:
		raise inst

    def EncodeBinString(self):
	cdglength = len(self.codinghistory + "\x00\x00")
	if (cdglength % 2) == 1:
	    cdglength -= 1
	return pack(self.formatstring.format(cdglength),
		self.title, self.author, self.reference, self.origindate,
		self.origintime, self.timereflow, self.timerefhigh, 
		self.version, self.umid, self.reserved, 
		self.codinghistory)

class MextChunk:
    """Class that represents the fields in a mpeg extension (mext) chunk"""
    formatstring = "<2sHHH4s"
    def __init__(self):
	self.soundinfo = "\x07\x00"
	self.framesize = 0
	self.ancildataln = 0
	self.ancildatadef = 0
	self.reserved = "\x00\x00\x00\x00"

    def __str__(self):
	soundinfoval, = unpack("<H", self.soundinfo)
	soundinfo = "{0:#016b}".format(soundinfoval)
	soundinfolist = []
	soundinfoflags = ["","","","","","","","","","","", "", \
		"FLAG_FREE_FORMAT_USED", "FLAG_VARIABLE_PADDING", \
		"FLAG_NO_PADDING", "FLAG_HOMOGENOUS_SOUND"]
	for x in range(15, 11, -1):
	    if int(soundinfo[x]) == 1:
		soundinfolist.append(soundinfoflags[x])
	return """SoundInfo value: {0} {1}
Frame Size: {2}
Ancillary Data Length: {3}
Ancillary Data Definition: {4}
""".format(soundinfo, soundinfolist, self.framesize, self.ancildataln,
	   self.ancildatadef)

    def GetMpegParam(self, mpeginfo):
	self.framesize = mpeginfo.framesize

    def DecodeBinString(self, header, chunksize):
	(self.soundinfo, self.framesize, self.ancildataln, self.ancildatadef, 
		self.reserved) = unpack(self.formatstring, header)

    def EncodeBinString(self):
	return pack(self.formatstring, self.soundinfo, self.framesize, 
		self.ancildataln, self.ancildatadef, self.reserved)

class FactChunk:
    """Class that represents the information contained in a Fact Chunk"""
    formatstring = "<L"
    def __init__(self):
	self.numsamples = 0

    def __str__(self):
	return "Number of Samples in File: {0}\n".format(self.numsamples)

    def GetMpegParam(self, mpegheader):
	self.numsamples = mpegheader.numsamples

    def DecodeBinString(self, header, chunksize):
	self.numsamples, = unpack(self.formatstring, header)

    def EncodeBinString(self):
	return pack(self.formatstring, self.numsamples)

class FmtChunk:
    """Class that represents the information in a Fmt Chunk"""
    formatstring = "<HHLLHHHHLHHHHLL"
    def __init__(self):
	self.compressioncode = 80
	self.numchannels = 0
	self.samplerate = 0
	self.byterate = 0
	self.blockalign = 0
	self.bitspersample = 65535
	self.subchunksize = 22
	self.headlayer = 0
	self.headbitrate = 0
	self.headmode = 0
	self.headmodeext = 0
	self.heademphasis = 0
	self.headflags = 0
	self.ptslow = 0
	self.ptshigh = 0

    def __str__(self):
	mpegflagsdef = ["","","","","","","","","","", "", \
		"ACM_MPEG_ID_MPEG1", "ACM_MPEG_PROTECTIONBIT", \
		"ACM_MPEG_ORIGINALHOME", "ACM_MPEG_COPYRIGHT", \
		"ACM_MPEG_PRIVATEBIT"]
	mpegflagslist = []
	mpegflags = "{0:#016b}".format(self.headflags)
	for x in range(15, 10, -1):
	    if int(mpegflags[x]) == 1:
		mpegflagslist.append(mpegflagsdef[x])
	subchunkstring = """MPEG Layer: {0}
MPEG Bitrate: {1}
MPEG Mode: {2}
MPEG Mode extension: {3}
MPEG emphasis: {4}
MPEG Header Flags: {5} {6}
MPEG PTS Low: {7}
MPEG PTS High: {8}
""".format( self.headlayer, self.headbitrate, self.headmode,
	    self.headmodeext, self.heademphasis, mpegflags, 
	    mpegflagslist, self.ptslow, self.ptshigh )

	fmtchunkstring = """Compression Code: {0}
Number of Channels: {1}
Sample Rate: {2}
Byte Rate: {3}
Block Align: {4}
Bits Per Sample: {5}
Sub-chunk size: {6}
""".format( self.compressioncode, self.numchannels, self.samplerate,
	    self.byterate, self.blockalign, self.bitspersample,
	    self.subchunksize)
	if self.subchunksize == 0:
	    return fmtchunkstring
	else:
	    return fmtchunkstring + subchunkstring

    def GetMpegParam(self, mpeginfo):
	self.numchannels = mpeginfo.numchannels
	self.samplerate = mpeginfo.samplerate
	self.byterate = mpeginfo.bitrate * 1000 / 8
	self.blockalign = mpeginfo.framesize
	self.headlayer = mpeginfo.fmtlayer
	self.headbitrate = mpeginfo.bitrate * 1000
	self.headmode = mpeginfo.fmtmode
	self.headmodeext = mpeginfo.fmtmodeext
	self.heademphasis = mpeginfo.fmtemphasis
	self.headflags = mpeginfo.fmtheadflags

    def __setattr__(self, attrname, value):
        #print "Setting {0} to {1}".format(attrname, value)
	self.__dict__[attrname] = value

    def DecodeBinString(self, header, chunksize):
	if chunksize == 40:
	    (self.compressioncode, self.numchannels, self.samplerate, self.byterate,
	     self.blockalign, self.bitspersample, self.subchunksize, self.headlayer,
	     self.headbitrate, self.headmode, self.headmodeext, self.heademphasis,
	     self.headflags, self.ptslow,
	     self.ptshigh) = unpack(self.formatstring, header)
	elif chunksize == 18:
            (self.compressioncode, self.numchannels, self.samplerate, self.byterate,
	     self.blockalign, self.bitspersample, self.subchunksize) = unpack(
	         "<HHIIHHH", header)
	elif chunksize == 16:
            (self.compressioncode, self.numchannels, self.samplerate, self.byterate,
	     self.blockalign, self.bitspersample) = unpack("<HHIIHH", header)
	    self.subchunksize = 0
	else:
	    raise Exception("Could not decode FMT chunk")

    def EncodeBinString(self):
	if self.compressioncode == 1:
	    return pack("<HHIIHHH", self.compressioncode, self.numchannels,
		self.samplerate, self.byterate, self.blockalign, 
		self.bitspersample, self.subchunksize)

	return pack(self.formatstring, self.compressioncode, self.numchannels,
		self.samplerate, self.byterate, self.blockalign, 
		self.bitspersample, self.subchunksize, self.headlayer,
		self.headbitrate, self.headmode, self.headmodeext, 
		self.heademphasis, self.headflags, self.ptslow, self.ptshigh) 

class MpegInfoDescriptor:
    """Class that represents the information contained in an MPEG header"""
    def __init__(self, mpegheader, filesize):
	mpegheader, = unpack(">L", mpegheader)
	headerbin = "{0:b}".format(mpegheader)
	#If headerbin[0:11] is not all ones, it is not a valid header
	
	MpegVerTable = (2.5, "reserved", 2, 1)
	MpegLyrTable = ("reserved", 3, 2, 1)
	FmtLyrTable = ("null", 1, 2, 4)
	FmtModeTable = (1, 2, 4, 8)
	FmtModeExtTable = (1, 2, 4, 8)
	Mpeg1L2BRTable = ('free', 32, 48, 56, 64, 80, 96, 112, 128, 160,
		          192, 224, 256, 320, 384 )
	Mpeg1L3BRTable = ('free', 32, 40, 48, 56, 64, 80, 96, 112, 128,
		          160, 192, 224, 256, 320 )
	Mpeg1SRTable = (44100, 48000, 32000, "reserved")
	MpegChanModeTable = (2, 2, 2, 1)

	self.mpegver = MpegVerTable[int(headerbin[11:13], 2)]
	self.mpeglyr = MpegLyrTable[int(headerbin[13:15], 2)]
	self.protectbit = headerbin[15]
	self.bitrate = Mpeg1L2BRTable[int(headerbin[16:20], 2)]
	self.samplerate = Mpeg1SRTable[int(headerbin[20:22], 2)]
	self.padding = headerbin[22]
	self.privatebit = headerbin[23]
	self.numchannels = MpegChanModeTable[int(headerbin[24:26], 2)]
	self.channelmode = int(headerbin[24:26], 2)
	self.modeext = int(headerbin[26:28], 2)
	self.copyrightbit = headerbin[28]
	self.originalbit = headerbin[29]
	self.emphasis = int(headerbin[30:32], 2)
	self.framesize = int( (144 * self.bitrate * 1000 / self.samplerate)
		              + int(self.padding) )
	self.datasize = filesize
	self.numsamples = int( self.datasize / self.framesize * 1152 )
	self.fmtlayer = FmtLyrTable[self.mpeglyr]
	self.fmtmode = FmtModeTable[self.channelmode]
	self.fmtmodeext = FmtModeExtTable[self.modeext]
	self.fmtemphasis = self.emphasis + 1
	self.fmtheadflags = int("0001" + self.protectbit + self.originalbit
		                 + self.copyrightbit + self.privatebit, 2 )
	self.mpegheader = mpegheader

class CDPFile:
    """Class implementation of chunked BWF wave file to ContentDepot(TM) specs"""
    def __init__(self):
	self.cart = CartChunk()
	self.bext = BextChunk()
	self.mext = MextChunk()
	self.fact = FactChunk()
	self.fmt = FmtChunk()
	self.datasize = 0
	self.mpegfilename = ""
	self.audiopointer = 0
	self.wavefilename = ""
	self.audiosrcfilename = ""

    def __str__(self):
	return "---FMT Chunk---\n{0}\n---FACT Chunk---\n{1}\n---MEXT Chunk---" \
		"\n{2}\n---BEXT Chunk---\n{3}\n---CART Chunk---" \
		"\n{4}\n".format(self.fmt, self.fact, self.mext, self.bext, self.cart)

    def ImportMpegFile(self, mpegfilename):
	mpegheader, self.datasize = GetMPEGHeaderFromFile(mpegfilename)
	self.audiosrcfilename = mpegfilename
	mpeginfo = MpegInfoDescriptor(mpegheader, self.datasize)
	self.mext.GetMpegParam(mpeginfo)
	self.fact.GetMpegParam(mpeginfo)
	self.fmt.GetMpegParam(mpeginfo) 
	
    def ExportMpegFile(self, mpegfilename):
	with open(self.audiosrcfilename, "rb") as f:
	    with open(mpegfilename, "wb") as m:
		f.seek(self.audiopointer)
		audio = f.read(self.fmt.blockalign)
		while (m.tell() < self.datasize) and audio:
		    m.write(audio)
		    audio = f.read(self.fmt.blockalign)
		    
    def __ReadWaveFile_old(self, wavefilename):
	foundchunklist = []
	with open(wavefilename, 'rb') as f:
	    data = f.read(12)
	    riff, riffsize, wave = unpack("<4sL4s", data)
	    chunktype = ""
	    while chunktype != "data":
		data = f.read(8)
		chunktype, chunksize = unpack("<4sL", data)
		#print chunktype, chunksize
		if hasattr(self, chunktype.rstrip()):
		    foundchunklist.append(chunktype.rstrip())
		    data = f.read(chunksize)
		    getattr(self, chunktype.rstrip()).DecodeBinString(data,
			    chunksize)
		if chunktype == "data":
		    self.audiopointer = f.tell()
		    self.datasize = chunksize
	    if self.fmt.compressioncode == 80:
		self.audiosrcfilename = wavefilename
	    else:
		self.audiosrcfilename = wavefilename
	return foundchunklist
    
    def MakeChunkDictionary(self, binDataBlock):
	ChunkDict = dict()
	ptr = 12
	#Skip the first 12 bytes
	chunktype = ""
	while ptr < len(binDataBlock):
	    data = binDataBlock[ptr:(ptr+8)]
	    ptr += 8
	    chunktype, chunksize = unpack("<4sL", data)
	    if chunktype == "data":
		ChunkDict[chunktype] = (ptr, chunksize)
	    else:
		ChunkDict[chunktype.rstrip()] = binDataBlock[ptr:(ptr+chunksize)]
	    ptr += chunksize

	for t, v in ChunkDict.iteritems():
	    if hasattr(self, t):
		getattr(self, t).DecodeBinString(
			v, len(v))
	    elif t == "data":
		self.audiopointer = v[0]
		self.datasize = v[1]

	return ChunkDict.keys()

    def SearchWaveDataBlob(self, binDataBlock):
	foundchunklist = []
	ptr = 0
	data = binDataBlock[ptr:(ptr+12)]
	ptr += 12
	riff, riffsize, wave = unpack("<4sL4s", data)
	chunktype = ""
	while chunktype != "data" and ptr < len(binDataBlock):
	    data = binDataBlock[ptr:(ptr+8)]
	    ptr +=8
	    chunktype, chunksize = unpack("<4sL", data)
	    #print chunktype, chunksize
	    foundchunklist.append(chunktype.rstrip())
	    if hasattr(self, chunktype.rstrip()):
		data = binDataBlock[ptr:(ptr+chunksize)]
		ptr += chunksize
	        getattr(self, chunktype.rstrip()).DecodeBinString(data,
			    chunksize)
	    elif chunktype == "data":
		#print "Found data chunk"
	        self.audiopointer = ptr
	        self.datasize = chunksize
	    else:
		ptr += chunksize
		#print "Skipping unknown chunk"

	return foundchunklist

    def ReadWaveFile(self, wavefilename):
	#Open wave file
	with open( wavefilename, 'rb') as f:
	    data = f.read(8192)
	#foundchunklist = self.SearchWaveDataBlob( data )
	foundchunklist = self.MakeChunkDictionary(data)
	if self.fmt.compressioncode == 80:
	    self.audiosrcfilename = wavefilename
	else:
	    self.audiosrcfilename = wavefilename

	return foundchunklist

    def WriteWaveFileHelper(self, wavefilename, chunklist, inputfile):
        #ChunkList = (self.fmt, self.fact, self.mext, self.bext, self.cart)
	#Chunks = [chunk.EncodeBinString() for chunk in ChunkList]
	#ChunkStuff = zip(["fmt ", "fact", "mext", "bext", "cart"], Chunks)
	HeaderString = ""
	for chunkname in chunklist:
	    chunkstring = getattr(self, str(chunkname).strip(" ")).EncodeBinString()
	    HeaderString = HeaderString + chunkname + pack("L", len(chunkstring)) + chunkstring
	HeaderString = HeaderString + chunkname + pack("L", len(chunkstring)) + chunkstring
	HeaderString = HeaderString + "data" + pack("L", self.datasize)

	HeaderString = "RIFF" + pack("L", len(HeaderString) + self.datasize + 4) \
	               + "WAVE" + HeaderString

	with open(inputfile, 'rb') as m:
	    with open(wavefilename, 'wb') as f:
		f.write(HeaderString)
		m.seek(self.audiopointer)
		audio = m.read(self.fmt.blockalign)
		while audio:
		    f.write(audio)
		    audio = m.read(self.fmt.blockalign)
		if (self.datasize % 2) == 1:
		    f.write('\x00')

    def WriteCompressedWaveFile(self, wavefilename):
	chunklist = ["fmt ", "fact", "mext", "bext", "cart"]
	self.WriteWaveFileHelper(wavefilename, chunklist, self.audiosrcfilename)

    def WritePCMWaveFile(self, wavefilename):
	chunklist = ["fmt ", "bext", "cart"]
	self.WriteWaveFileHelper(wavefilename, chunklist, self.audiosrcfilename)

def GetMPEGHeaderFromFile(filename):
    '''Auxiliary function to get the mpeg header from an MPEG file'''
    with open(filename, "rb") as f:
	possibleheader = f.read(4)
	mpegheader, = unpack(">L", possibleheader)
	headerbin = "{0:b}".format(mpegheader)
	if re.match( r'1111111111.*', headerbin):
	    return possibleheader, os.path.getsize(filename)
	else:
	    raise InvalidMPEGDataError("No Sync Signal found at start of MPEG data")

def RunTests():
    pass

def CondepTests():
    MyConDepThing = CDPFile()
    MyConDepThing.cart.title = "Another Condep file"
    MyConDepThing.cart.artist = "John McMellen"
    MyConDepThing.cart.cutnum = "12345"
    MyConDepThing.cart.title = "AllThi21 090223 SGMT 01 A Billboard All Things Considered Everg"
    MyConDepThing.cart.artist = ""
    MyConDepThing.cart.cutnum = "74040"
    MyConDepThing.cart.outcue = '"...first the news.'
    MyConDepThing.cart.startdate = "2009/02/23"
    MyConDepThing.cart.starttime = "01:00:00"
    MyConDepThing.cart.enddate = "2010/02/19"
    MyConDepThing.cart.endtime = "23:59:00"

    #MyConDepThing.WriteCompressedWaveFile("thing.wav")

    MyConDepThing.ImportMpegFile("CarTalk__170_SGMT01.mp2")
    MyConDepThing.WriteCompressedWaveFile("atestfile.wav")
    MyConDepThing.ReadWaveFile("atestfile.wav")
    MyConDepThing.ExportMpegFile("atestfile.mp2")
    MyConDepThing.ReadWaveFile("258SiobhanMichaelSeg1.wav")
    MyConDepThing.ExportMpegFile("Michael.mp2")
    print MyConDepThing.cart.ExportXMLValues()
    MyConDepThing.cart.ImportXMLValues("<?xml version='1.0' ?><cart>" \
	    "<version>0101</version><title>XML Title</title>" \
	    "<artist>John XML</artist><cutnum>00001</cutnum><clientid></clientid>" \
	    "<category></category><classification></classification><outcue></outcue>" \
	    "<startdate>2000/07/07</startdate><starttime>01:23:45</starttime>" \
	    "<enddate>2020/09/09</enddate><endtime>22:01:32</endtime>" \
	    "<appid>PythonUtil2</appid><appver>3.0</appver><userdef></userdef>" \
	    "<zerodbref>0</zerodbref><posttimers>{1}</posttimers><url></url>" \
	    "<tagtext>{0}</tagtext></cart>".format('<program-associated-data><property name="OwnerIdentifier" value="ContentDepot"/><property name="Identifier" value="001"/><property name="Title" value="Talk about ContentDepot"/><property name="Artist" value="PRSS"/><property name="Album" value="ContentDepot Test Program"/><property name="Genre" value="101"/><property name="CommentTitle" value="This is a comment"/><property name="Comment" value="These are test and placeholder fields for ContentDepot PAD support in files. They are currently generated from static fields in the ContentDepot Portal database. Send email to prssplanning@npr.org if you have questions."/></program-associated-data>', '<timer type="MRK ">112000</timer><timer type="SEC1">152533</timer><timer type="">4294967295</timer><timer type="">4294967295</timer><timer type="">4294967295</timer><timer type="">4294967295</timer><timer type="">4294967295</timer><timer type="EOD ">201024</timer>'))
    print MyConDepThing.cart
    CCfile = CDPFile()
    CCfile.ReadWaveFile("CC_0101.wav")
    print CCfile
    print CCfile.cart.ExportXMLValues()
    CCfile.WritePCMWaveFile("CC_0101_john.wav")

if __name__ == "__main__":
    #RunTests()
    #MakeAHeader()
    CondepTests()



