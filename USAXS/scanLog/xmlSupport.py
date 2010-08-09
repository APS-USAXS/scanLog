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
from xml.dom import minidom
from xml.etree import ElementTree

#**************************************************************************

def readPvlistXML(xmlFile):
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
    config = {}
    pvListFile = os.path.join(baseDir,'pvlist.xml')
    config['pvList'] = readPvlistXML(pvListFile)
    return(config)

#**************************************************************************

def __parseElement__(element):
    print(element.name)
    for attribute in element.xpathEval('@*'):
    	print("  @ " + attribute.name)
    for child in element.xpathEval('*'):
        __parseElement__(child)

#**************************************************************************

if __name__ == "__main__":
   if (len(sys.argv) == 2):
   	   pwd = sys.argv[1]
   else:
   	   pwd = '.'
   config = readConfigurationXML(pwd)
   print "PVs named in configuration:"
   import pprint
   pprint.pprint(config)
   #for pv in config['pvList']:
   #    print pv['pv']
