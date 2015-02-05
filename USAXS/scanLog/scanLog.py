#!/bin/env python

'''watch EPICS PVs for user scan events and log to XML file'''


import os
import sys
import time
import epics        # PyEpics
import xmlSupport   # local support for the log file of USAXS scans
import updates      # local support for configuration (PV list)
import pyRestTable  # formatted tabular output


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
    ch = connectPvAndMonitor(pv)
    db[pv] = ch
    return ch


def doEpicsPvConnectEvent(**kw):
    '''responds to an EPICS connect event on a process variable (PV)'''
    conn = kw['conn']
    # otherwise, do nothing


def doEpicsPvMonitorEvent(pvname=None, char_value=None, **kw):
    '''responds to an EPICS monitor on a process variable (PV)'''
    global db
    db[pvname + ',count'] += 1  # count number of times this PV updated


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
    t = pyRestTable.Table()
    t.labels = ["time stamp", "# received", "PV name", "value"]
    for pv in sorted(pvList):
        timeStr = timeToStr(db[pv].timestamp)
        t.rows.append( (timeStr, db[pv+',count'], pv, db[pv].value) )
    print "#" + ">"*60
    print "# reportEpicsPvs(): " + timeToStr(time.time())
    print t.reST(),
    print "#" + "<"*60


def updateScanLog(lastScanningState):
    '''create or modify the scan log file based on current scanning state'''
    global cfg
    global db
    global pvTag
    scanningState = db[pvTag['scanning']].value
    if scanningState != lastScanningState and lastScanningState != 'initial':
        directory = db[pvTag['directory']].value
        fileName = db[pvTag['file']].value
        datafile = os.path.join(directory, fileName)
        title = db[pvTag['title']].value
        number = str(db[pvTag['number']].value)
        scanmacro = db[pvTag['scanmacro']].value
        if str(scanningState) in ( 'scanning', '1', 1 ):
            updates.startScanEntry(
                cfg['scanLog'], number, datafile, title, scanmacro)
        elif str(scanningState) in ( 'no', '0', 0 ):
            updates.endScanEntry(
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
    message += " starting on HOST=" + os.environ['HOSTNAME']
    message += " by user=" + os.environ['USER']
    print message
    sys.stdout.flush()

    db = {}
    pvList = []
    pvTag = {}
    baseDir = '/home/beams/USAXS/Documents/eclipse/USAXS/scanLog'
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
