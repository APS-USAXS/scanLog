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
import CaChannel
import time
import os
import sys
import xmlSupport  # local support for the log file of USAXS scans
import scanlog     # local support for configuration (PV list)


#-------------------------------------------------------------


def setupEpicsConnection(pvEntry):
    '''prepare the data structures to monitor 
    this EPICS PV and initiate the monitor
    @param pvEntry: EPICS PV name string
    @return: EPICS PV channel object'''
    global db
    pv = pvEntry['pv']
    db[pv + ',count'] = 0
    db[pv + ',time'] = 0
    ch = connectPvAndMonitor(pv)
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
    db[pv + ',time'] = time.time()  # Python time monitor was received


def connectPvAndMonitor(pv):
    '''connect with EPICS PV and initiate monitor'''
    ch = CaChannel.CaChannel()
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

def timeToStr(time_seconds):
    '''format the time as ISO8601 human-readable string'''
    local = time.localtime(time_seconds)
    return time.strftime("%Y-%m-%d %H:%M:%S", local)


def reportEpicsPvs(pvList):
    '''print all the PV values to stdout'''
    global db
    dict = {}
    format = "%20s\t%10s\t%36s\t%s"
    for pv in pvList:
        value = db[pv+',value']
        last_update = db[pv+',time']
        count = db[pv+',count']
        timeStr = timeToStr(last_update)
        dict[timeStr + pv] = format % (timeStr, count, pv, value)
    keys = dict.keys()
    keys.sort()
    now = timeToStr(time.time())
    print "# reportEpicsPvs(): " + now
    print "#"+format % ("time stamp", "# received", "PV name", "value")
    for key in keys:
        print dict[key]


def updateScanLog(lastScanningState):
    '''create or modify the scan log file based on current scanning state'''
    global cfg
    global db
    global pvTag
    scanningState = db[pvTag['scanning']+',value']
    if (scanningState != lastScanningState):
        if lastScanningState != 'initial':  # but not this case
            directory = db[pvTag['directory']+',value']
            fileName = db[pvTag['file']+',value']
            datafile = os.path.join(directory, fileName)
            title = db[pvTag['title']+',value']
            number = db[pvTag['number']+',value']
            scanmacro = db[pvTag['scanmacro']+',value']
            if scanningState == 'scanning':
                scanlog.startScanEntry(
                    cfg['scanLog'], number, datafile, title, scanmacro)
            elif scanningState == 'no':
                scanlog.endScanEntry(
                    cfg['scanLog'], number, datafile)
            else:
                print "this should not happen, state = ", scanningState
    return scanningState


#-------------------------------------------------------------

def errorReport(message):
    '''report an error to stdout'''
    print "#------------------------------"
    print "# ", time.ctime(), " Python error report:"
    print message
    print "#------------------------------"

#-------------------------------------------------------------

SCANLOG_XML = 'scanlog.xml'
PVLIST_XML = 'pvlist.xml'

def main():
    ''' monitor the EPICS PVs for the scan and update the XML file '''
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
    cfg = xmlSupport.readConfigurationXML(os.path.join(baseDir, PVLIST_XML))
    cfg['scanLog'] = os.path.join(baseDir, cfg['scanLogFile'])

    for pvEntry in cfg['pvList']:
        ch = setupEpicsConnection(pvEntry)     # remember this for the calls to ch.pend_event()
        pvList.append(pvEntry['pv'])
        pvTag[pvEntry['tag']] = pvEntry['pv']
        ch.pend_event()

    lastScanningState = "initial"
    reportInterval_seconds = 30*60  # dump out the PV values to stdout
    nextReport = time.time()        # make first reportEpicsPvs right away

    print "#------------------------------"
    print "# ", time.ctime(), " Started"
    print "#------------------------------"
    while 1:
        ch.pend_event() # receives all PV monitors, not just for ch
        try:
            lastScanningState = updateScanLog(lastScanningState)
        except StandardError, error_message:
            errorReport(error_message)
        if time.time() >= nextReport:
            nextReport = time.time() + reportInterval_seconds
            reportEpicsPvs(pvList)
        sys.stdout.flush()
        time.sleep(1)   # Is it possible to miss a transition at 1 Hz?

#-------------------------------------------------------------

if __name__ == "__main__":
    main()
