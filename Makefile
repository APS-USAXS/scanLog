# scanLog/Makefile

DATE_STRING = $(shell date '+%Y%m%d-%H%M%S')


start ::
	./scanlog.csh start

stop ::
	./scanlog.csh stop

restart ::
	./scanlog.csh restart

checkup ::
	./scanlog.csh checkup

