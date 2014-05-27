#!/bin/env python

'''watch EPICS PVs for user scan events and log to XML file'''

#-------------------------------------------------------------

import os
import sys
import time
import epics        # PyEpics
import xmlSupport   # local support for the log file of USAXS scans
import scanlog      # local support for configuration (PV list)


#-------------------------------------------------------------


def setupEpicsConnection(pvEntry):
    '''
    prepare data structures to monitor this EPICS PV and initiate the monitor
    
    :param str pvEntry: EPICS PV name string
    :return obj: instance of epics.PV(): EPICS PV channel object
    '''
    global db
    pv = pvEntry['pv']
    db[pv + ',count'] = 0
    db[pv + ',time'] = 0
    ch = connectPvAndMonitor(pv)
    db[pv + ',ch'] = ch
    return ch


def doEpicsPvConnectEvent(**kw):
    '''responds to an EPICS connect event on a process variable (PV)'''
    conn = kw['conn']
    # otherwise, do nothing


def doEpicsPvMonitorEvent(pvname=None, char_value=None, **kw):
    '''responds to an EPICS monitor on a process variable (PV)'''
    global db
    db[pvname + ',value'] = char_value
    db[pvname + ',count'] += 1  # number of times this PV updated
    db[pvname + ',time'] = time.time()  # Python time monitor was received


def connectPvAndMonitor(pv):
    '''connect with EPICS PV and initiate monitor'''
    ch = epics.PV(pv, 
                  connection_callback=doEpicsPvConnectEvent, 
                  callback=doEpicsPvMonitorEvent)
    return ch

def timeToStr(time_seconds):
    '''format the time as ISO8601 human-readable string'''
    local = time.localtime(time_seconds)
    return time.strftime("%Y-%m-%d %H:%M:%S", local)


def reportEpicsPvs(pvList):
    '''print all the PV values to stdout'''
    global db
    xref = {}
    fmt = "%20s\t%10s\t%36s\t%s"
    for pv in pvList:
        value = db[pv+',value']
        last_update = db[pv+',time']
        count = db[pv+',count']
        timeStr = timeToStr(last_update)
        xref[timeStr + pv] = fmt % (timeStr, count, pv, value)
    keys = xref.keys()
    keys.sort()
    now = timeToStr(time.time())
    print "#" + ">"*60
    print "# reportEpicsPvs(): " + now
    print "#"+fmt % ("time stamp", "# received", "PV name", "value")
    for key in keys:
        print xref[key]
    print "#" + "<"*60


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
    ''' monitor the EPICS PVs for the scan and update the XML file'''
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
    if len(cfg) == 0:
        print "ERROR: could not read the configuration file"
        return
    cfg['scanLog'] = os.path.join(cfg['local_www_dir'], cfg['scanLogFile'])

    for pvEntry in cfg['pvList']:
        setupEpicsConnection(pvEntry)     # remember this for the calls to ch.pend_event()
        pvList.append(pvEntry['pv'])
        pvTag[pvEntry['tag']] = pvEntry['pv']
        epics.ca.poll()

    lastScanningState = "initial"
    reportInterval_seconds = 30*60  # dump out the PV values to stdout
    nextReport = time.time()        # make first reportEpicsPvs right away

    print "#------------------------------"
    print "# ", time.ctime(), " Started"
    print "#------------------------------"
    while 1:
        epics.ca.poll() # receives all PV monitors, not just for ch
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


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
