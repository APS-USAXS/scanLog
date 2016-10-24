#!/usr/bin/python

'''Record starting and ending times of USAXS scans'''

#**************************************************************************

import datetime
import os
import sys
from xml.etree import ElementTree
import wwwServerTransfers
import xmlSupport

#**************************************************************************

MACROS_ALLOWED_TO_LOG = ('uascan sbuascan FlyScan sbFlyScan pinSAXS WAXS USAXSImaging'.split())
processing_queue = None # singleton: there is one, and only one, event processing queue

#**************************************************************************


def usage():
    ''' in case we forget '''
    print 'usage:  updates.py start|end number fileName "the title" specScanMacro'


def buildID(number, fileName):
    ''' return the unique scan index ID based on scan number and file name '''
    return "%s:%s" % (number, fileName)


def timestamp():
    '''modified ISO8601 time: yyyy-mm-dd hh:mm:ss'''
    return str(datetime.datetime.now()).split('.')[0]


def startScanEntry(scanLogFile, number, fileName, title, macro):
    ''' Start a new scan in the XML file '''
    if not macro in MACROS_ALLOWED_TO_LOG:
        return  # ignore this one
    scanID = buildID(number, fileName)
    
    event = {
             'number': number,
             'phase': 'start',
             'id': scanID,
             'type': macro,
             'title': title,
             'timestamp': timestamp(),
             'file': fileName,
             'xml_file_name': scanLogFile,
             }
    queue = get_event_queue_object()
    queue.add_event(event)   # process event in a different thread


def endScanEntry(scanLogFile, number, fileName):
    ''' Set the ending time for the scan in the XML file '''
    scanID = buildID(number, fileName)  # index using scanID (above)

    event = {
             'number': number,
             'phase': 'end',
             'id': scanID,
             'timestamp': timestamp(),
             'file': fileName,
             'xml_file_name': scanLogFile,
             }
    queue = get_event_queue_object()
    queue.add_event(event)   # process event in a different thread


def event_processing(fifo, callback_function=None):
    '''
    process the event queue and add to XML file
    
    This processing is handled in a separate thread.
    The thread is managed by the EventQueue() class.
    Processing can take some time, especially when appending to
    a large XML file.
    
    :param [event] fifo: list of events (the queue)
    :param obj callback_function: method to call at the end of this method

    .. note:: Reading the entire XML file at this point makes the process
        a bit slower but allows another process to edit the XML file,
        such as to periodically remove old entries from the file.

        Skipping the step to read/parse the file might be faster if the
        external process were not used occasionally to shorten the XML file.

    '''
    xml_file_name = None
    doc = None

    # process each event in the queue
    for event in fifo:
        if doc is None:
            # load and parse the XML file using lxml.etree
            xml_file_name = event['xml_file_name']
            doc = xmlSupport.openScanLogFile(xml_file_name)
            if doc is None:
                print "ERROR: Could not open file: " + xml_file_name
                return

        if event['phase'] == 'start':
            scanNode = xmlSupport.locateScanID(doc, scanID)
            if scanNode is not None:
                print "ERROR: One or more scans matches in the log file."
                return
         
            root = doc.getroot()
            scanNode = ElementTree.Element('scan')
            scanNode.set('number', event['number'])
            scanNode.set('state', 'scanning')
            scanNode.set('id', event['scanID'])
            scanNode.set('type', event['macro'])
         
            # put this scan at the end of the list
            root.append(scanNode)
         
            xmlSupport.appendTextNode(doc, scanNode, 'title', event['title'])
            xmlSupport.appendTextNode(doc, scanNode, 'file', event['fileName'])
            xmlSupport.appendDateTimeNode(doc, scanNode, 'started', event['timestamp'])
         
            xmlSupport.flagRunawayScansAsUnknown(doc, scanID)

        elif event['phase'] == 'end':
            scanNode = xmlSupport.locateScanID(doc, event['scanID'])
            if scanNode is None:
                #print "ERROR: Could not find that scan in the log file."
                return
            if (scanNode.get('state') == 'scanning'):
                scanNode.set('state', 'complete')   # set scan/@state="complete"
                xmlSupport.appendDateTimeNode(doc, scanNode, 'ended', event['timestamp'])

        else:
            msg = 'unexpected scan event phase: ' + event['phase']
            raise RuntimeError(msg)

    # write the XML to disk
    # TODO set demo=False   With above, fixes Trac ticket #9
    xmlSupport.writeXmlDocToFile(xml_file_name, doc)

    wwwServerTransfers.scpToWebServer(xml_file_name, 
                  os.path.split(xml_file_name)[-1], demo = False)

    # check if the queue has more events to be processed
    if callback_function is not None:
        callback_function()             # inform the caller this thread is done


def get_event_queue_object():
    '''
    (create and) return the singleton EventQueue instance
    '''
    global processing_queue
    if processing_queue is None: # ensure this is a singleton
        processing_queue = EventQueue()
    return processing_queue


class EventQueue(object):
    '''
    queue, process, and store scan events in the XML file in a separate thread
    '''

    def __init__(self):
        '''
        set up the event processor in a separate thread
        '''
        global processing_queue
        if processing_queue is not None: # ensure this is a singleton
            raise RuntimeError('EventQueue() is a singleton.  Do not make more than one instance.')
        processing_queue = self

        self.fifo = []      # the event queue
        self.processing = False
    
    def add_event(self, *event):
        '''
        add an instrument scan event to the queue (actually a FIFO)
        
        Run the processing step.  If processing is already running,
        the callback will catch up with the new queue entries eventually.
        '''
        self.fifo.append(event)
        self.process_queue()
    
    def callback(self):
        '''
        check the queue and process any remaining events
        
        Since the processing can take some time, it is done in a separate thread.
        During that time, additional events might be queued.
        Ultimately, this callback from the end of the processing method,
        will ensure that the queue is emptied.
        '''
        self.processing = False
        if len(self.fifo) > 0:
            self.process_queue()

    def process_queue(self):
        '''
        prepare to process events and append them to the XML file
        
        Since the processing can take some time, it is done in a separate thread.
        '''
        if len(self.fifo) == 0 or self.processing:
            return
        self.processing = True
        work_queue = list(self.fifo)

        self.fifo = self.fifo[len(work_queue):]
        thread = threading.Thread(target=event_processing, 
                                  args=(work_queue, self.callback))
        thread.start()


#-------------------------------------------------

xmlFile = 'scanlog.xml'

if __name__ == "__main__":
    if len(sys.argv) != 6:
        # TODO: use argparse package
        usage()
        sys.exit()

    scriptname, mode, number, datafile, title, macro = sys.argv
    
    # This main() is test code.  The standard support starts with pvSupport.py 

    if (mode == 'started'):
        startScanEntry(xmlFile, number, datafile, title, macro)
    elif (mode == 'ended'):
        endScanEntry(xmlFile, number, datafile)
    else:
        usage()
        sys.exit()


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
