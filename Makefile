
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################

DATE_STRING = $(shell date '+%Y%m%d-%H%M%S')


start ::
	./scanlog.csh start

stop ::
	./scanlog.csh stop

restart ::
	./scanlog.csh restart

checkup ::
	./scanlog.csh checkup

