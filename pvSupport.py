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
    pv = pvEntry['pv']
    pvList.append(pv)
    db[pv + ',count'] = 0
    db[pv + ',time'] = 0
    db[pv + ',ch'] = watchThis(pv)

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
    scanningState = db[pvTag['scanning']+',value']
    if (scanningState != lastScanningState):
        # report()
	number = db[pvTag['number']+',value']
	directory = db[pvTag['directory']+',value']
	fileName = db[pvTag['file']+',value']
	title = db[pvTag['title']+',value']
	datafile = os.path.join(directory, fileName)
	if scanningState == 'ON':
	    scanlog.startScanEntry(cfg['scanLog'], number, datafile, title)
	elif scanningState == 'OFF':
	    scanlog.endScanEntry(cfg['scanLog'], number, datafile)
	else:
	    print "this should not happen, state = ", scanningState
    return scanningState

#-------------------------------------------------------------

if __name__ == "__main__":
    message = "# " + time.ctime()
    message += " PID=" + repr(os.getpid())
    message += " starting on HOST=" + os.environ['HOST']
    message += " by user=" + os.environ['USER']
    print message
    sys.stdout.flush()

    db = {}
    pvList = []
    pvTag = {}
    baseDir = '/home/beams/S32USAXS/jemian/scanLog'
    cfg = xmlSupport.readConfigurationXML(baseDir)
    cfg['scanLog'] = os.path.join(baseDir,'scanlog.xml')

    for pvEntry in cfg['pvList']:
        setup(pvEntry)
	pvTag[pvEntry['tag']] = pvEntry['pv']

    lastValue = db[pvTag['scanning']+',value']

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
    		lastValue = update(lastValue)
	except StandardError, error_message:
		print "#------------------------------"
		print "# ", time.ctime(), " Python error report:"
		print error_message
		print "#------------------------------"
    	#report()
    	time.sleep(1)
