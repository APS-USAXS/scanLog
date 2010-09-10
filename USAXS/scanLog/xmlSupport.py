#!/usr/bin/env python

'''
 read XML configuration files into a common data structure

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
'''

import os.path
import sys
import time
from xml.etree import ElementTree
# SEE https://subversion.xor.aps.anl.gov/trac/bcdaext/browser/pvrrd/xmlSupport.py
# for pretty XML format
from xml.dom import minidom

#**************************************************************************

def readPvlistXML(xmlFile):
    '''get the list of PVs to monitor from the XML file'''
    doc = ElementTree.parse(xmlFile)
    db = []
    for element in doc.findall('EPICS_PV'):
        arr = {}
        arr['desc'] = element.text.strip()
        for attribute in element.attrib.keys():
            arr[attribute] = element.attrib[attribute].strip()
        db.append(arr)
    return(db)

#**************************************************************************

def readConfigurationXML(baseDir):
    '''locate the PV configuration from XML into memory'''
    config = {}
    pvListFile = os.path.join(baseDir, 'pvlist.xml')
    config['pvList'] = readPvlistXML(pvListFile)
    return(config)

#**************************************************************************

def openScanLogFile(xmlFile):
    '''open the XML file with ElemenetTree
        return the doc (doc.getroot() to get the root node)'''
    return ElementTree.parse(xmlFile)

#**************************************************************************

def locateScanID(doc, id):
    '''find the XML scan entry with matching id attribute
        return XML node or None if not found
    '''
    result = None
    #query = "scan/[@id='%s']" % id
    for node in doc.findall("scan"):
        if node.get("id") == id:
            result = node
            break
    return result

#**************************************************************************

def flagRunawayScansAsUnknown(doc, id):
    '''sometimes, a scan ends without this program finding out'''
    for node in doc.findall("scan"):            # look for any scan ...
        if node.get("state") == "scanning":     # with state="scanning" ...
            if node.get("id") != id:            # but not the newest node ...
                node.set("state", "unknown")    # THIS node is not scanning anymore

#**************************************************************************

def readFileAsLines(filename):
    '''open a file and read all of it into 
        memory as a list separated by line breaks'''
    # FIXME needs error handling
    f = open(filename, 'r')
    buf = f.read()
    f.close()
    return buf.split("\n")

#**************************************************************************

def writeLinesInFile(filename, lines):
    '''write a list of lines to a file'''
    # FIXME needs error handling
    f = open(filename, 'w')
    f.write("\n".join(lines))
    f.close()
    return

#**************************************************************************

def prettyXml(element):
    '''indent written XML nicely'''
    # FIXME poor introduction of whitespace - DO NOT USE YET
    txt = ElementTree.tostring(element)
    return minidom.parseString(txt).toprettyxml()

#**************************************************************************

def writeScanLogFile(xmlFile, doc):
    '''write the XML doc to a file'''
    doc.write(xmlFile, encoding="UTF-8")
    # splice in the reference to the XSLT at the top of the file (on line 2)
    xsltRef = '<?xml-stylesheet type="text/xsl" href="scanlog.xsl" ?>'
    lines = readFileAsLines(xmlFile)
    lines.insert(1, xsltRef)
    writeLinesInFile(xmlFile, lines)
    return

#**************************************************************************

def appendTextNode(doc, parent, tag, value):
    '''append a text node to the XML document'''
    elem = ElementTree.Element(tag)
    elem.text = value
    parent.append(elem)

#**************************************************************************

def appendDateTimeNode(doc, parent, tag):
    '''append a date/time node to the XML document'''
    elem = ElementTree.Element(tag)
    elem.set('date', xmlDate())
    elem.set('time', xmlTime())
    parent.append(elem)

#**************************************************************************

def xmlDate():
    '''current date, for use in XML file (ISO8601)'''
    str = time.strftime('%Y-%m-%d')    # XML date format
    return str

#**************************************************************************

def xmlTime():
    '''current time, for use in XML file (ISO8601)'''
    str = time.strftime('%H:%M:%S')    # XML time format
    return str

#**************************************************************************


if __name__ == "__main__":
    if (len(sys.argv) == 2):
        pwd = sys.argv[1]
    else:
        pwd = '.'
    config = readConfigurationXML(pwd)
    #print "PVs named in configuration:"
    #import pprint
    #pprint.pprint(config)

    doc = openScanLogFile('scanlog.xml')
    scan = locateScanID(doc, '43:/share1/USAXS_data/2010-03/03_24_setup.dat')
    print scan
    root = doc.getroot()
    appendTextNode(doc, root, "bewilderment", "is a state of mind")
    appendDateTimeNode(doc, root, "timestamp")
    #print prettyXml(root)
    writeScanLogFile('test.xml', doc)
