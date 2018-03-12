#!/usr/bin/python

'''Record starting and ending times of USAXS scans'''

#**************************************************************************

import datetime
import os
import sys
import threading
from xml.etree import ElementTree
import xmlSupport
from reporting import errorReport, printReport

path = os.path.dirname(__file__)
path = os.path.join(path, "..")
sys.path.append(os.path.abspath(path))
from livedata import wwwServerTransfers

#**************************************************************************

MACROS_ALLOWED_TO_LOG = ('uascan sbuascan FlyScan sbFlyScan pinSAXS SAXS WAXS USAXSImaging'.split())
processing_queue = None # singleton: there is one, and only one, event processing queue

#**************************************************************************


def usage():
    ''' in case we forget '''
    print 'usage:  updates.py start|end number fileName "the title" specScanMacro'


def buildID(number, data_file_name):
    ''' return the unique scan index ID based on scan number and file name '''
    return "%s:%s" % (number, data_file_name)


def timestamp():
    '''modified ISO8601 time: yyyy-mm-dd hh:mm:ss'''
    return str(datetime.datetime.now()).split('.')[0]


def startScanEntry(scanLogFile, number, data_file_name, title, macro):
    ''' Start a new scan in the XML file '''
    if not macro in MACROS_ALLOWED_TO_LOG:
        return  # ignore this one
    scanID = buildID(number, data_file_name)

    event = {
             'number': number,
             'phase': 'start',
             'scanID': scanID,
             'macro': macro,
             'title': title,
             'timestamp': timestamp(),
             'datetime_full': str(datetime.datetime.now()),
             'data_file_name': data_file_name,
             'xml_file_name': scanLogFile,
             }
    queue = get_event_queue_object()
    printReport("scan start detected", scanID, use_separators=False)
    queue.add_event(event)   # process event in a different thread


def endScanEntry(scanLogFile, number, data_file_name):
    ''' Set the ending time for the scan in the XML file '''
    scanID = buildID(number, data_file_name)  # index using scanID (above)

    event = {
             'number': number,
             'phase': 'end',
             'scanID': scanID,
             'timestamp': timestamp(),
             'datetime_full': str(datetime.datetime.now()),
             'data_file_name': data_file_name,
             'xml_file_name': scanLogFile,
             }
    queue = get_event_queue_object()
    printReport("scan end detected", scanID, use_separators=False)
    queue.add_event(event)   # process event in a different thread


def event_processing(fifo, q_id, callback_function=None):
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
            printReport(q_id + ': opening XML file', use_separators=False)
            doc = xmlSupport.openScanLogFile(xml_file_name)
            if doc is None:
                errorReport(q_id + ": Could not open file: " + xml_file_name)
                return
            printReport(q_id + ': XML file opened', use_separators=False)

        scanID = event.get('scanID')
        if scanID is None:
            errorReport(q_id + ": Could not find 'scanID' in the event data: " + str(event))
            continue

        if event['phase'] == 'start':
            printReport(q_id + ': add event to XML', 'start', use_separators=False)
            scanNode = xmlSupport.locateScanID(doc, scanID)
            if scanNode is not None:
                errorReport(q_id + ": One or more scans matches in the log file.")
                continue

            root = doc.getroot()
            scanNode = ElementTree.Element('scan')
            scanNode.set('number', event['number'])
            scanNode.set('state', 'scanning')
            scanNode.set('id', event['scanID'])
            scanNode.set('type', event['macro'])

            # put this scan at the end of the list
            root.append(scanNode)

            xmlSupport.appendTextNode(doc, scanNode, 'title', event['title'])
            xmlSupport.appendTextNode(doc, scanNode, 'file', event['data_file_name'])
            xmlSupport.appendDateTimeNode(doc, scanNode, 'started', event['datetime_full'])

            xmlSupport.flagRunawayScansAsUnknown(doc, scanID)

        elif event['phase'] == 'end':
            printReport(q_id + ': add event to XML', 'end', use_separators=False)
            scanNode = xmlSupport.locateScanID(doc, scanID)
            if scanNode is None:
                errorReport(q_id + ": Could not find scan in the log file: " + str(scanID))
                # TODO: could mark the scan end received with no matching start
                continue
            if (scanNode.get('state') == 'scanning'):
                scanNode.set('state', 'complete')   # set scan/@state="complete"
                xmlSupport.appendDateTimeNode(doc, scanNode, 'ended', event['datetime_full'])

        else:
            msg = q_id + ': unexpected scan event phase: ' + event['phase']
            raise RuntimeError(msg)

    try:
        # write the XML to disk
        # TODO set demo=False   With above, fixes Trac ticket #9
        printReport(q_id + ': starting XML file write', use_separators=False)
        xmlSupport.writeXmlDocToFile(xml_file_name, doc)
        printReport(q_id + ': XML file written', use_separators=False)
    except Exception as exc:
        printReport(q_id + ': Exception while writing XML', str(exc))

    try:
        printReport(q_id + ': transfer to WWW server started', use_separators=False)

        source = xml_file_name
        path = os.path.dirname(source)
        files = "scanlog.xml scanlog.log"
        #printReport(q_id + ': transferring:', message=source, use_separators=False)
        target = wwwServerTransfers.SERVER_WWW_LIVEDATA
        command = wwwServerTransfers.RSYNC
        command += " -rRtz %s %s" % (files, target)
        printReport(q_id + ': command', message=command, use_separators=False)
        owd = os.getcwd()
        os.chdir(path)
        wwwServerTransfers.execute_command(command)
        os.chdir(owd)

        printReport(q_id + ': transfer to WWW server complete', use_separators=False)
    except Exception as exc:
        printReport(q_id + ': Exception while copying to WWW server', str(exc))


    # check if the queue has more events to be processed
    if callback_function is not None:
        callback_function(q_id)      # inform the caller this thread is done


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
        self.q_id = 0

    def add_event(self, *event):
        '''
        add an instrument scan event to the queue (actually a FIFO)

        Run the processing step.  If processing is already running,
        the callback will catch up with the new queue entries eventually.
        '''
        self.fifo.append(*event)
        self.process_queue()

    def callback(self, q_id):
        '''
        check the queue and process any remaining events

        Since the processing can take some time, it is done in a separate thread.
        During that time, additional events might be queued.
        Ultimately, this callback from the end of the processing method,
        will ensure that the queue is emptied.
        '''
        self.processing = False
        if len(self.fifo) > 0:
            msg = " # new events = " + str(len(self.fifo))
            printReport(q_id + ": processing additional events in queue", msg, use_separators=False)
            self.process_queue()
            printReport(q_id + ": thread completed", use_separators=False)

    def process_queue(self):
        '''
        prepare to process events and append them to the XML file

        Since the processing can take some time, it is done in a separate thread.
        '''
        if len(self.fifo) == 0 or self.processing:
            return
        self.processing = True
        self.q_id += 1
        qStr = 'Thread-' + str(self.q_id)
        work_queue = list(self.fifo)

        self.fifo = self.fifo[len(work_queue):]
        thread = threading.Thread(target=event_processing,
                                  args=(work_queue, qStr, self.callback))
        printReport(qStr + ": thread starting", thread.name, use_separators=False)
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
