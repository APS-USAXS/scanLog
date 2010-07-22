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

import sys
import libxml2
import os.path

#**************************************************************************

def readPvlistXML(xmlFile):
    doc = libxml2.parseFile(xmlFile)
    context = doc.xpathNewContext()
    db = []
    for element in context.xpathEval('//PV_LIST/EPICS_PV'):
    	result = element.xpathEval('./@pv')
    	pv = result[0].content.strip()
    	arr = {}
    	arr['desc'] = element.content.strip()
	for attribute in element.xpathEval('@*'):
	    arr[attribute.name] = attribute.content.strip()
    	db.append(arr)
    context.xpathFreeContext()
    doc.freeDoc()
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
   print "list OF PVs named in configuration:"
   for pv in config['pvList']:
       print pv['pv']
