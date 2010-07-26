#!/bin/tcsh
#
# chkconfig: - 98 98
# description: Record starting and ending times of USAXS scans
#
# processname: scanlog

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################

# 2008-12-12,PRJ: set the right paths for BCDA Python+EPICS support at APS
source /APSshare/epics/startup/2007_07_31/epicsSetup.cshrc

setenv PYTHON  /APSshare/bin/python
# 2009-06-09,PRJ: /APSshare/bin/python --> ImportError: No module named libxml2
# standard sysAdmin-supplied Python has it.
setenv PYTHON  python

setenv HOME_DIR /home/beams/S15USAXS
setenv BASE_DIR ${HOME_DIR}/Documents/eclipse/USAXS/scanLog
setenv WWW_DIR  /data/www/livedata
setenv THIS_FILE ${BASE_DIR}/scanlog.csh
setenv SCRIPT  ${BASE_DIR}/pvSupport.py
setenv LOGFILE ${WWW_DIR}/scanlog.log
setenv PIDFILE ${WWW_DIR}/scanlog.pid

switch ($1)
  case "start":
        ${PYTHON} ${SCRIPT} >>& ${LOGFILE} &
        setenv PID $!
        /bin/rm ${PIDFILE}
        /bin/echo ${PID} > ${PIDFILE}
        /bin/echo "started ${PID}: ${PYTHON} ${SCRIPT}"
        /bin/echo "# `/bin/date`: started ${PID}: ${SCRIPT}" >>& ${LOGFILE}
        breaksw
  case "stop":
        setenv PID `/bin/cat ${PIDFILE}`
        /bin/ps -p ${PID} > /dev/null
        setenv NOT_EXISTS $?
        if (${NOT_EXISTS}) then
             /bin/echo "not running ${PID}: ${SCRIPT}"
        else
             kill ${PID}
             /bin/echo "stopped ${PID}: ${SCRIPT}"
             /bin/echo "# `/bin/date`: stopped ${PID}: ${SCRIPT}" >>& ${LOGFILE}
        endif
        breaksw
  case "restart":
        $0 stop
        $0 start
        breaksw
  case "checkup":
        set pid = `/bin/cat ${PIDFILE}`
	set test = `/bin/ps -p ${pid} --no-header -o pid`
	if (${pid} != ${test}) then
	  echo "# `/bin/date` could not identify running process ${pid}, restarting" >>& ${LOGFILE}
	  echo `${THIS_FILE} restart` >& /dev/null
	endif
        breaksw
  default:
        /bin/echo "Usage: $0 {start|stop|restart|checkup}"
        breaksw
endsw
