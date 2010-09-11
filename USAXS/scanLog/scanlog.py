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
from xml.etree import ElementTree
import xmlSupport

#**************************************************************************

MACROS_ALLOWED_TO_LOG = ('uascan', 'sbuascan')

#**************************************************************************

def usage():
    ''' in case we forget '''
    print 'usage:  scanlog.py started|ended number fileName "the title" specScanMacro'

def buildID(number, fileName):
    ''' return the unique scan index ID based on scan number and file name '''
    return "%s:%s" % (number, fileName)

def startScanEntry(scanLogFile, number, fileName, title, macro):
    ''' Start a new scan in the XML file '''
    if not macro in MACROS_ALLOWED_TO_LOG:
        return  # ignore this one
    scanID = buildID(number, fileName)
    doc = xmlSupport.openScanLogFile(scanLogFile)
    scanNode = xmlSupport.locateScanID(doc, scanID)
    if scanNode != None:
        print "ERROR: One or more scans matches in the log file."
        return
    #---
    root = doc.getroot()
    scanEntry = ElementTree.Element('scan')
    scanEntry.set('number', number)
    scanEntry.set('state', 'scanning')
    scanEntry.set('id', scanID)
    scanEntry.set('type', macro)
    # put this scan at the end of the list
    root.append(scanEntry)
    #---
    xmlSupport.appendTextNode(doc, scanEntry, 'title', title)
    xmlSupport.appendTextNode(doc, scanEntry, 'file', fileName)
    xmlSupport.appendDateTimeNode(doc, scanEntry, 'started')
    #---
    xmlSupport.flagRunawayScansAsUnknown(doc, scanID)
    #---
    xmlSupport.writeXmlDocToFile(scanLogFile, doc)


def endScanEntry(scanLogFile, number, fileName):
    ''' Set the ending time for the scan in the XML file '''
    scanID = buildID(number, fileName)  # index using scanID (above)
    doc = xmlSupport.openScanLogFile(scanLogFile)
    scanNode = xmlSupport.locateScanID(doc, scanID)
    if scanNode==None:
        #print "ERROR: Could not find that scan in the log file."
        return
    #---
    if (scanNode.get('state')=='scanning'):
        scanNode.set('state', 'complete')   # set scan/@state="complete"
        xmlSupport.appendDateTimeNode(doc, scanNode, 'ended')
        xmlSupport.writeXmlDocToFile(scanLogFile, doc)


#-------------------------------------------------

xmlFile = 'scanlog.xml'

if __name__ == "__main__":
    if len(sys.argv) != 6:
        usage()
        sys.exit()

    (scriptname, mode, number, datafile, title, macro) = sys.argv
    
    # This main() is test code.  The standard support starts with pvSupport.py 

    if (mode == 'started'):
        startScanEntry(xmlFile, number, datafile, title, macro)
    elif (mode == 'ended'):
        endScanEntry(xmlFile, number, datafile)
    else:
        usage()
        sys.exit()