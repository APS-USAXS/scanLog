#!/bin/csh

########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################

# perhaps this is only used for development, not production

setenv PYTHON /APSshare/bin/python

setenv TARGET xmlSupport.py
setenv TARGET pvSupport.py

${PYTHON} ${TARGET}
