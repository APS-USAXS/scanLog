#!/bin/env python

'''
log EPICS data into RRD files

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
'''

#-------------------------------------------------------------

import ca
from CaChannel import *
import time
import os
import sys
import xmlSupport  # local support for the log file of USAXS scans
import scanlog     # local support for configuration (PV list)

#-------------------------------------------------------------


db = {}
pvList = []

#-------------------------------------------------------------


def setup(pvEntry):
    pv = pvEntry['pv']
    pvList.append(pv)
    db[pv + ',count'] = 0
    db[pv + ',time'] = 0
    ch = watchThis(pv)
    db[pv + ',ch'] = ch
    return ch

def demoEpicsCallback(epics_args, user_args):
    chan = user_args[0]
    pv = chan.name()
    value = epics_args["pv_value"]
    db[pv + ',value'] = value
    # how many times this PV has given a monitored callback
    db[pv + ',count'] += 1
    timeNow = time.time()
    # Python time this script received a monitored callback
    ### Could use this to update as monitored events are received
    ### yet throttle the update frequency to no more than once every ?? seconds
    ### For now, use the "update all every N seconds" method and ignore time
    db[pv + ',time'] += time.time()

def watchThis(pv):
    ch = CaChannel()
    try:
        ch.searchw(pv)
        user_args = (ch)
        ch.add_masked_array_event(ca.DBR_STRING, 1, ca.DBE_VALUE, demoEpicsCallback, user_args)
    except:
        message = time.ctime()
        message += " could not find " + pv
        print message
        sys.stdout.flush()
        ch = ''
    return (ch)

def report():
    for pv in pvList:
        value = db[pv+',value']
        last_update = db[pv+',time']
        print pv, '\t', value, '\t', last_update

def update(lastScanningState):
    print pvTag['scanning']
    print db
    scanningState = db[pvTag['scanning']+',value']
    if (scanningState != lastScanningState):
        # report()
        number = db[pvTag['number']+',value']
        directory = db[pvTag['directory']+',value']
        fileName = db[pvTag['file']+',value']
        title = db[pvTag['title']+',value']
        datafile = os.path.join(directory, fileName)
        scanmacro = db[pvTag['scanmacro']+',value']
        if scanningState == 'scanning':
            scanlog.startScanEntry(cfg['scanLog'], number, datafile, title, scanmacro)
        elif scanningState == 'no':
            scanlog.endScanEntry(cfg['scanLog'], number, datafile)
        else:
            print "this should not happen, state = ", scanningState
    return scanningState

#-------------------------------------------------------------

def main():
    ''' monitor the EPICS PVs for the scan and update the XML file '''
    message = "# " + time.ctime()
    message += " PID=" + repr(os.getpid())
    message += " starting on HOST=" + os.environ['HOST']
    message += " by user=" + os.environ['USER']
    print message
    sys.stdout.flush()

    db = {}
    pvList = []
    pvTag = {}
    baseDir = '/home/beams/S15USAXS/Documents/eclipse/USAXS/scanLog'
    cfg = xmlSupport.readConfigurationXML(baseDir)
    cfg['scanLog'] = os.path.join(baseDir,'scanlog.xml')

    for pvEntry in cfg['pvList']:
        ch = setup(pvEntry)
        pvTag[pvEntry['tag']] = pvEntry['pv']

    lastScanningState = "unknown"
    
    # FIXME Why aren't the PVs connecting here?
    # This code should not be needed.
    for i in range(5):	# allow PVs to connect
    	time.sleep(1)
        ch.pend_event()

    print "#------------------------------"
    print "# ", time.ctime(), " Started"
    print "#------------------------------"
    while 1:
        pv = pvList[0]
        ch = db[pv + ',ch']
        ch.pend_event()
        # all monitors will be received even if just
        # one PV's pend_event is called
        try:
            lastScanningState = update(lastScanningState)
        except StandardError, error_message:
            print "#------------------------------"
            print "# ", time.ctime(), " Python error report:"
            print error_message
            print "#------------------------------"
        #report()
        time.sleep(1)

#-------------------------------------------------------------

if __name__ == "__main__":
    main()
