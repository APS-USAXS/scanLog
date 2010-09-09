#!/usr/bin/python

'''
Record starting and ending times of USAXS scans

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
'''

#**************************************************************************

import sys
import time
# TODO refactor XML support using ElementTree
import xml.dom.minidom
import xml.dom.ext
import xml.xpath

#**************************************************************************

def usage():
   print 'usage:  scanlog.py started|ended number fileName "the title"'

def appendTextNode(doc, scanEntry, tag, value):
    elem = doc.createElement(tag)
    scanEntry.appendChild(elem)
    node = doc.createTextNode(value)
    elem.appendChild(node)

def appendDateTimeNode(doc, scanEntry, tag):
    elem = doc.createElement(tag)
    scanEntry.appendChild(elem)
    elem.setAttribute('date', xmlDate())
    elem.setAttribute('time', xmlTime())

def xmlDate():
    str = time.strftime('%Y-%m-%d')    # XML date format
    return str

def xmlTime():
    str = time.strftime('%H:%M:%S')    # XML time format
    return str

def buildID(number, fileName):
    return "%s:%s" % (number, fileName)

def locateScanID(doc, scanID):
    query = '//scan[@id="%s"]' % scanID
    return xml.xpath.Evaluate(query, doc)

def startScanEntry(scanLogFile, number, fileName, title):
    scanID = buildID(number, fileName)
    doc = openScanLogFile(scanLogFile)
    result = locateScanID(doc, scanID)
    if len(result)>0:
        print "ERROR: One or more scans matches in the log file."
	return
    # put this scan at the end of the list
    scanEntry = doc.createElement('scan')
    lastScanEntry = doc.childNodes[len(doc.childNodes)-1]
    lastScanEntry.appendChild(scanEntry)
    #---
    scanEntry.setAttribute('number', number)
    scanEntry.setAttribute('state', 'scanning')
    scanEntry.setAttribute('id', scanID)
    #---
    appendTextNode(doc, scanEntry, 'title', title)
    appendTextNode(doc, scanEntry, 'file', fileName)
    #---
    appendDateTimeNode(doc, scanEntry, 'started')
    #---
    # now look for any other scans with @state='scanning' and change state to 'unknown'
    for e in xml.xpath.Evaluate('//scan[@state="scanning"]', doc):
        if (e.getAttribute('id') != scanID):    # don't change the new node
	    e.setAttribute('state', 'unknown')  # but THIS node is not scanning anymore
    #---
    writeScanLogFile(scanLogFile, doc)
    return

def endScanEntry(scanLogFile, number, fileName):
    # find scan based on ID (above)
    scanID = buildID(number, fileName)
    doc = openScanLogFile(scanLogFile)
    result = locateScanID(doc, scanID)
    if len(result)==0:
        print "ERROR: Could not find that scan in the log file."
	return
    elif len(result)>1:
        print "ERROR: More than one scan matches in the log file! (Should not happen)"
	return
    scanEntry = result[0]
    if (scanEntry.getAttribute('state')=='scanning'):
        scanEntry.setAttribute('state', 'complete')   # set scan/@state="complete"
        appendDateTimeNode(doc, scanEntry, 'ended')
        writeScanLogFile(scanLogFile, doc)
    return

def openScanLogFile(xmlFile):
    scanLog = xml.dom.minidom.parse(xmlFile)
    return scanLog

def writeScanLogFile(xmlFile, scanLog):
    f = open(xmlFile, 'w')
    xml.dom.ext.PrettyPrint(scanLog, stream=f)
    f.close()
    return

#-------------------------------------------------

xmlFile = 'scanlog.xml'

if __name__ == "__main__":
     if len(sys.argv) != 5:
     	 usage()
     	 sys.exit()

     mode = sys.argv[1]
     number = sys.argv[2]
     datafile = sys.argv[3]
     title = sys.argv[4]

     if (mode == 'started'):
     	 startScanEntry(xmlFile, number, datafile, title)
     elif (mode == 'ended'):
     	 endScanEntry(xmlFile, number, datafile)
     else:
     	 usage()
     	 sys.exit()
