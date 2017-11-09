# -*- coding: utf-8 -*-

import re

logfile = "geoserver.log"
convertedlog = "convertedlog.csv"

class geoserverLog():
    logid = ""
    logtime = ""    
    logtype = ""
    logsource = ""
    logcontent = []
    logepsg = 0
    lograw = ""
    logWKT = ""
    isMapRequest = False
    requestsize = [None,None]
    
    def __init__(self,entrynum,logtext):
        self.logid = int(entrynum)        
        editLog = logtext.split("\n")
        
        # the first line contains information about time, logtype and source of the log-message source
        # the first 23 characters are the timestamp
        self.logtime = editLog[0][:23]        
        
        # the logtype are the following 5 chars
        self.logtype = editLog[0][24:28]   
        
        # the rest of the message until the first "-" is the source java-class reporting the log-entry
        self.logsource = editLog[0][29:].split(" - ")[0]
        leftover = " ".join([ x for i,x in enumerate(editLog[0][29:].split(" - ")) if (i > 0) ])
        self.logcontent = "\n".join([leftover] + editLog[1:])
        
        # ---------------- WMS REQUEST LOGGING ---------------------
        if self.logsource == "[geoserver.wms]":
            #print(self.logcontent)
            if re.search("Request: getMap",self.logcontent) != None:
                self.isMapRequest = True
                
                self.requestsize[0] = int(re.search("Height = [0-9]+",self.logcontent).group(0)[9:])
                self.requestsize[1] = int(re.search("Width = [0-9]+",self.logcontent).group(0)[8:])
                self.logepsg = re.search("SRS = EPSG:[0-9]+",self.logcontent).group(0)[11:]
                self.lograw = re.search("RawKvp = .+}",self.logcontent).group(0)[9:]
                
                bbox = re.search("Bbox = SRSEnvelope\[.+\]",self.logcontent).group(0)[19:].replace("]","").replace(","," :").split(" : ")
                print(bbox)
                self.logWKT = "POLYGON(( {} {},{} {},{} {},{} {},{} {} ))".format(bbox[0],bbox[2],bbox[1],bbox[2],bbox[1],bbox[3],bbox[0],bbox[3],bbox[0],bbox[2])
                print(self.logWKT)
        

def isLineStartingWithTime(textline):
    """Regex-match to a valid Date/Time stamp at the begining of a line. If matched, return True
       example match-date/time: 2017-11-09 18:34:15,832"""
    
    if re.match("^([0-9]{4})-([01][0-9])-([0-3][0-9]) ([0-2][0-9]):([0-5][0-9]):([0-5][0-9]),[0-9]{3}",textline):
        return True
    else:
        return False

def separateLogEntries(logfile):
    detectedLogLines = []
    with open(logfile, 'r') as f:
        loglines = f.readlines()
        collectedLogLine = ""
        for i, logline in enumerate(loglines):
            # separate the log-entries by their beginning timestamp
            if isLineStartingWithTime(logline):
                # store old logline
                detectedLogLines.append(collectedLogLine)
                # clear for new logline            
                collectedLogLine = logline
            else:
                # add to existing logline
                collectedLogLine += logline
    
    return detectedLogLines


glog = separateLogEntries(logfile)

with open(convertedlog, 'w') as w:
    for i, gent in enumerate(glog):
        a = geoserverLog(i,gent)
        if a.logsource == "[geoserver.wms]":
            if a.isMapRequest:
                print("entry {} at {}: {} pixels, EPSG:{}".format(a.logid,a.logtime,a.requestsize[0]*a.requestsize[1],a.logepsg))
                w.write("{};{};{};{};{};{};{};{}\n".format(a.logtime.split(" ")[0],a.logtime.split(" ")[1],a.logsource,a.logepsg,a.requestsize[0],a.requestsize[1],a.logWKT,a.lograw))