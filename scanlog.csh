#!/bin/tcsh
#
# chkconfig: - 98 98
# description: Record starting and ending times of USAXS scans
#
# processname: scanlog

###### crontab -e task #########################
# build: http://usaxs.xray.aps.anl.gov/livedata/scanlog.xml
#  */5 * * * * /home/beams/USAXS/Documents/eclipse/USAXS/scanLog/scanlog.csh checkup 2>&1 /dev/null
################################################


#setenv PYTHON  /APSshare/epd/rh6-x86_64/bin/python
setenv PYTHON  /APSshare/anaconda/x86_64/bin/python
setenv HDF5_DISABLE_VERSION_CHECK 2

setenv HOME_DIR /home/beams/USAXS
setenv BASE_DIR ${HOME_DIR}/Documents/eclipse/USAXS/scanLog
setenv WWW_DIR  /share1/local_livedata
setenv THIS_FILE ${BASE_DIR}/scanlog.csh
setenv SCRIPT  ${BASE_DIR}/scanLog.py
setenv LOGFILE ${WWW_DIR}/scanlog.log
setenv PIDFILE ${WWW_DIR}/scanlog.pid

setenv SNAME $0
setenv SELECTION $1

/bin/echo "#${SNAME} ${SELECTION}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"  >>& ${LOGFILE} 
/bin/echo "# date: `date`"  >>& ${LOGFILE} 
#/bin/echo "# env: `env|sort`"  >>& ${LOGFILE} 

switch (${SELECTION})
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
        ${SNAME} stop
        ${SNAME} start
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
        /bin/echo "Usage: ${SNAME} {start|stop|restart|checkup}"
        breaksw

endsw

/bin/echo "#${SNAME} ${SELECTION}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"  >>& ${LOGFILE} 



########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
