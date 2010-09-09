#!/usr/bin/env python
'''
Created on Feb 21, 2009

@author: Pete
@purpose: Read a file with a list of possible SPEC file names
          and search for USAXS scans (uascan and sbuascan).
          Note information about those found and report back in
          XML format.
'''

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################


import time


def dofile(filename):
    '''process one SPEC data file, looking for USAXS scans'''
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
            if (scanType == 'uascan') or (scanType == 'sbuascan'):
                id = parts[1]
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
                    entry = build_entry(scanType, id, title, filename,
                        startdate, starttime, enddate, endtime)
                    DB[sortkey] = entry
    f.close


def build_entry(type, number, title, filename,
                        startdate, starttime, enddate, endtime):
    '''return an XML element from the supplied parameters'''
    fmt = """
  <scan
      state='complete'
      type='%s'
      number='%s'
      id='%s'
    >
    <title>%s</title>
    <file>%s</file>
    <started date='%s' time='%s'/>
    <ended date='%s' time='%s'/>
  </scan>
    """
    #
    # TODO: This could fail if (XML) invalid characters are in the title
    #
    id = "%s:%s" % (number, filename)
    buf = fmt % (
        type, number, id, title, filename,
        startdate, starttime, enddate, endtime)
    return buf.strip("\n")


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


if __name__ == '__main__':
    # create usaxs-spec-files.txt using the command line:
    #   locate .dat | grep /data | grep -v /archive | grep -v .Trash | grep -v livedata > usaxs-spec-files.txt
    filelist = 'usaxs-spec-files.txt'
    DB = {}
    f = open(filelist)
    for line in f:
        filename = line.strip()
        if is_spec_file(filename):
            dofile(filename)
    f.close()
    KEYS = DB.keys()
    KEYS.sort()
    print "<?xml version='1.0' encoding='UTF-8'?>"
    print "<?xml-stylesheet type='text/xsl' href='scanlog.xsl' ?>"
    print "<USAXS_32ID>"
    for item in KEYS:
        print DB[item]
    print "</USAXS_32ID>"
