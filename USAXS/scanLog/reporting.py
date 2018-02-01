'''
manage the console reporting for the scanLog tool
'''

import datetime

def printReport(title, message = '', use_separators=True):
    '''print a message to stdout'''
    if use_separators:
        print "#" + "-"*30
    msg = "# " + str(datetime.datetime.now())
    msg += " " + title
    if len(str(message)) > 0:
        msg += ": " + str(message)
    print msg
    if use_separators:
        print "#" + "-"*30

def errorReport(message):
    '''report an error to stdout'''
    printReport("Python error report", message=message)


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
