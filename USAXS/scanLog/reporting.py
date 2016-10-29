'''
manage the console reporting for the scanLog tool
'''

import datetime

def printReport(title, message = '', use_separators=True):
    '''print a message to stdout'''
    if use_separators:
      print "#" + "-"*30
    print "# " + str(datetime.datetime.now()) + " " + title + ": " + str(message)
    if use_separators:
      print "#" + "-"*30

def errorReport(message):
    '''report an error to stdout'''
    printReport("Python error report", message)


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
