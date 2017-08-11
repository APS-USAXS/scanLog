#!/usr/bin/env python
'''
search a file for USAXS scans (uascan and sbuascan)

:author: Pete Jemian

Read a file with a list of possible SPEC file names
and search for USAXS scans (uascan and sbuascan).
Note information about those found and report back in
XML format.

.. note:: 
   This routine would be improved immensely by using standard
   XML library support instead of writing strings in XML statements.
   The standard library support would avert problems such as
   invalid characters in the titles.

'''


import sys
import time
from xml.etree import ElementTree
import xmlSupport


ROOT_ELEMENT = "USAXS_SCAN_LOG"

SCAN_TYPES_LOGGED = ['uascan', 'sbuascan', 'FlyScan', 'pinSAXS', 'SAXS', 'WAXS', 'USAXSImaging']

def dofile(filename):
    '''process one SPEC data file, looking for USAXS scans, add to DB'''
    global DB
    # test it first to see if it is a SPEC data file
    next_comment_is_title = False
    scan_start_found = False
    next_comment_is_scanover = False
    f = open(filename)
    for line in f:
        signal = line[0:2]
        if signal == "#S":
            parts = line.strip().split()
            scanType = parts[2]
            scan_start_found = False
            if scanType in SCAN_TYPES_LOGGED:
                scanid = parts[1]
                scan_start_found = True
        elif signal == "#D":
            if scan_start_found:
                timestamptxt = line.strip()[3:]
                timestruct = time.strptime(timestamptxt, "%c")
                startdate = time.strftime("%Y-%m-%d", timestruct)
                starttime = time.strftime("%H:%M:%S", timestruct)
                sortkey = time.mktime(timestruct)
                next_comment_is_title = True
        elif signal == "#L":
            if scan_start_found:
                next_comment_is_scanover = True
        elif signal == "#C":
            if scan_start_found:
                if next_comment_is_title:
                    next_comment_is_title = False
                    title = line[3:].strip()
                elif next_comment_is_scanover:
                    next_comment_is_scanover = False
                    timestamptxt = ' '.join(line.split()[1:6]).strip(' .')
                    timestruct = time.strptime(timestamptxt, "%c")
                    enddate = time.strftime("%Y-%m-%d", timestruct)
                    endtime = time.strftime("%H:%M:%S", timestruct)
                    # all information is gathered for one scan entry
                    entry = build_entry(scanType, scanid, title, filename,
                        startdate, starttime, enddate, endtime)
                    # add this to the DB dictionary
                    DB[sortkey] = entry
    f.close


def build_entry(scantype, number, title, filename,
                        startdate, starttime, enddate, endtime):
    '''return a dictionary from the supplied parameters'''
    xref = dict(
                id = "%s:%s" % (number, filename),
                type = scantype,
                number = number,
                title = title,
                file = filename,
                starteddate = startdate,
                startedtime = starttime,
                endeddata = enddate,
                endedtime = endtime,
                state = 'complete',
                )
    return xref


def is_spec_file(filename):
    '''filename is a spec file
       only if the first three lines
       begin with #F, #E, and #D
    '''
    test = False
    f = open(filename)
    line = f.readline()
    if line.split()[0] == "#F":
        #line = f.readline()
        #print filename, "|", line, "|"
        #if line.split()[0] == "#E":
        #    line = f.readline()
        #    if line.split()[0] == "#D":
        test = True
    f.close()
    return test

def writeXmlFile(xmlFile, DB):
    '''write the XML file with the supplied dictionary'''
    # create the XML structure in memory
    root = ElementTree.Element(ROOT_ELEMENT)
    node = ElementTree.Element("created.by")
    node.text = sys.argv[0]
    node.set("datetime", time.ctime())
    root.append(node)

    for key in sorted(DB.keys()):
        xref = DB[key]
        """
            <scan id="29:/share1/USAXS_data/2010-03/03_24_setup.dat" number="29"
                state="complete">
                <title>GC Bob 12kev USAXS</title>
                <file>/share1/USAXS_data/2010-03/03_24_setup.dat</file>
                <started date="2010-03-24" time="10:12:02" />
                <ended date="2010-03-24" time="10:17:31" />
            </scan>
        """
        scanNode = ElementTree.Element("scan")
        for item in ('id', 'number', 'state', 'type'):
            scanNode.set(item, xref[item])
        for item in ('title', 'file'):
            subNode = ElementTree.Element(item)
            subNode.text = xref[item]
            scanNode.append(subNode)
        for item in ('started', 'ended'):
            subNode = ElementTree.Element(item)
            for part in ('date', 'time'):
                subNode.set(part, xref[item+part])
            scanNode.append(subNode)
        root.append(scanNode)
    #---
    # wrap it in an ElementTree instance, and save as XML
    xmlSupport.writeXmlDocToFile(xmlFile, ElementTree.ElementTree(root))


def main():
    global DB
    # create usaxs-spec-files.txt using the command line:
    #   locate .dat | grep /share1/USAXS_data | grep -v /archive | grep -v .Trash | grep -v livedata > usaxs-spec-files.txt
    filelist = 'usaxs-spec-files.txt'
    #filelist = 'short-usaxs-spec-files.txt'
    DB = {}
    f = open(filelist)
    for line in f:
        filename = line.strip()
        if is_spec_file(filename):
            dofile(filename)
    f.close()
    #---
    writeXmlFile("test.xml", DB)
    #---
    print "Found %d scans" % len(DB)


if __name__ == '__main__':
    main()


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
