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


def setup(pvEntry):
    '''prepare the data structures to monitor 
    this EPICS PV and initiate the monitor
    @param pvEntry: EPICS PV name string
    @return: EPICS PV channel object'''
    global db
    global pvList
    pv = pvEntry['pv']
    pvList.append(pv)
    db[pv + ',count'] = 0
    db[pv + ',time'] = 0
    ch = watchThis(pv)
    db[pv + ',ch'] = ch
    return ch

def doEpicsPvMonitorEvent(epics_args, user_args):
    '''responds to an EPICS monitor on a process variable (PV)'''
    global db
    chan = user_args[0]
    pv = chan.name()
    value = epics_args["pv_value"]
    db[pv + ',value'] = value
    db[pv + ',count'] += 1  # number of times this PV updated
    db[pv + ',time'] += time.time()  # Python time monitor was received
    ### Could use this to updateScanLog as monitored events are received
    ### yet throttle the updateScanLog frequency to no more than once every ?? seconds
    ### For now, use the "updateScanLog all every N seconds" method and ignore time

def watchThis(pv):
    '''connect with EPICS PV and initiate monitor'''
    ch = CaChannel()
    try:
        ch.searchw(pv)
        user_args = (ch)
        ch.add_masked_array_event(ca.DBR_STRING, 
              1, ca.DBE_VALUE, doEpicsPvMonitorEvent, user_args)
    except:
        message = time.ctime()
        message += " could not find " + pv
        print message
        sys.stdout.flush()
        ch = ''
    return (ch)

def report():
    '''print all the PV values to stdout'''
    global db
    global pvList
    for pv in pvList:
        value = db[pv+',value']
        last_update = db[pv+',time']
        print pv, '\t', value, '\t', last_update

def updateScanLog(lastScanningState):
    '''create or modify the scan log file based on current scanning state'''
    global cfg
    global db
    global pvTag
    print pvTag['scanning']
    print db
    scanningState = db[pvTag['scanning']+',value']
    # do not trigger when last state is "initial"
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
    ''' monitor the EPICS PVs for the scan and updateScanLog the XML file '''
    global cfg
    global db
    global pvTag
    global pvList
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

    lastScanningState = "initial"
    
    # FIXME Why aren't the PVs connecting here?
    # This code should not be needed.
    for i in range(5):	# allow PVs to connect
        time.sleep(1)
        ch.pend_event()
        lastScanningState = updateScanLog(lastScanningState)
        report()

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
            lastScanningState = updateScanLog(lastScanningState)
        except StandardError, error_message:
            print "#------------------------------"
            print "# ", time.ctime(), " Python error report:"
            print error_message
            print "#------------------------------"
        #report()
        time.sleep(1)   # Is it possible to miss a transition at 1 Hz?

#-------------------------------------------------------------

if __name__ == "__main__":
    main()
