#!/bin/csh

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################

# 2008-12-12,PRJ: set the right paths for BCDA Python+EPICS support at APS
source /APSshare/epics/startup/2007_07_31/epicsSetup.cshrc

setenv TARGET xmlSupport.py
setenv TARGET pvSupport.py

python ${TARGET}
