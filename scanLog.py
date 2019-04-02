#!/bin/env python

'''watch EPICS PVs for user scan events and log to XML file'''


import getpass
import os
os.environ['HDF5_DISABLE_VERSION_CHECK'] = '2'
import platform
import sys
import time
import epics        # PyEpics
import xmlSupport   # local support for the log file of USAXS scans
import updates      # local support for configuration (PV list)
import pyRestTable  # formatted tabular output
from reporting import errorReport, printReport


#-------------------------------------------------------------


def setupEpicsConnection(pvEntry):
    '''
    prepare data structures to monitor this EPICS PV and initiate the monitor

    :param str pvEntry: EPICS PV name string
    :return obj: instance of epics.PV(): EPICS PV channel object
    '''
    global db, as_string
    pv = pvEntry['pv']
    db[pv + ',count'] = 0
    ch = connectPvAndMonitor(pv)
    db[pv] = ch
    as_string[pv] = pvEntry.get("string", "false").lower() in ("t", "true")
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
    global db, as_string
    t = pyRestTable.Table()
    t.labels = ["time stamp", "# received", "PV name", "value"]
    for pv in sorted(pvList):
        timeStr = timeToStr(db[pv].timestamp)
        if as_string[pv]:
            value = db[pv].char_value
        else:
            value = db[pv].value
        t.rows.append( (timeStr, db[pv+',count'], pv, value) )
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
        directory = db[pvTag['directory']].char_value
        fileName = db[pvTag['file']].char_value
        datafile = os.path.join(directory, fileName)
        title = db[pvTag['title']].char_value
        number = str(db[pvTag['number']].value)
        scanmacro = db[pvTag['scanmacro']].char_value
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

SCANLOG_XML = 'scanlog.xml'
PVLIST_XML = 'pvlist.xml'


def main():
    ''' monitor the EPICS PVs for the scan and update the XML file'''
    global as_string
    global cfg
    global db
    global pvTag
    global pvList
    host = platform.node().split('.')[0]
    user = getpass.getuser()
    message = "# "
    message += " PID=" + repr(os.getpid())
    message += " starting on HOST=" + host
    message += " by user=" + user
    printReport("scanLog startup", message, use_separators=False)
    sys.stdout.flush()

    as_string = {}
    db = {}
    pvList = []
    pvTag = {}
    baseDir = '/home/beams/USAXS/Documents/eclipse/USAXS/scanLog'
    cfg = xmlSupport.readConfigurationXML(os.path.join(baseDir, PVLIST_XML))
    if len(cfg) == 0:
        errorReport("could not read the configuration file")
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

    printReport("starting main event loop", use_separators=False)
    while True:
        epics.ca.poll() # receives all PV monitors, not just for ch
        try:
            lastScanningState = updateScanLog(lastScanningState)
        except StandardError, error_message:
            errorReport(error_message)
        if time.time() >= nextReport:
            nextReport = time.time() + reportInterval_seconds
            reportEpicsPvs(pvList)
        sys.stdout.flush()
        time.sleep(0.1)   # Is it possible to miss a transition at 10 Hz?

#-------------------------------------------------------------

if __name__ == "__main__":
    main()
