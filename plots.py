#!/usr/bin/env python

'''make plots of the last *n* scans in the scanlog'''


import os
import spec2nexus.spec
import xmlSupport


SCANLOG = '/share1/local_livedata/scanlog.xml'


class Scan(object):
    
    def __init__(self, title, data_file, scan_type, scan_number, idstr):
        self.title = title
        self.scan_type = scan_type
        self.data_file = data_file
        self.scan_number = int(scan_number)
        self.identification = idstr
        # TODO: make a safe ID, suitable for use as an HDF5 label (<63 char, none odd)
        self.Q = None
        self.I = None
    
    def __str__(self, *args, **kwargs):
        return self.scan_type + ": " + self.title
    
    def getData(self):
        if self.scan_type in ('uascan', 'sbuascan'):
            # TODO: implement a cache of already reduced data
            spec = spec2nexus.spec.SpecDataFile(self.data_file)
            spec_scan = spec.getScan(self.scan_number)
            # TODO: need to reduce the USAXS raw data
            print spec_scan.scanCmd
        elif self.scan_type in ('FlyScan'):
            pass
        elif self.scan_type in ('pinSAXS'):
            pass
        elif self.scan_type in ('WAXS'):
            pass
        else:
            pass


def ok_to_plot(scan):
    ok = False
    # TODO: test if this scan is already in the cache of known scans with data
    if scan.attrib['type'] in ('uascan', 'sbuascan'):
        if scan.attrib['state'] in ('scanning', 'complete'):
            if os.path.exists(scan.find('file').text.strip()):
                ok = True
    elif scan.attrib['type'] in ('FlyScan', ):
        if scan.attrib['state'] in ('complete', ):
            # TODO: test that HDF5 data file exists
            ok = True
    return ok


def last_n_scans(xml_log_file, number_scans):
    xml_doc = xmlSupport.openScanLogFile(SCANLOG)

    # make sure only state="complete" scans are selected
    # TODO: make sure data file exists
    scans = [scan for scan in xml_doc.findall('scan') if ok_to_plot(scan)]

    return scans[-number_scans:]


def main():
    scans = [Scan(scan.find('title').text.strip(),
                 scan.find('file').text.strip(),
                 scan.attrib['type'],
                 scan.attrib['number'],
                 scan.attrib['identification'],
             ) for scan in last_n_scans(SCANLOG, 5)]
    print '\n'.join(map(str, scans))
    print '\n'.join([_.identification for _ in scans])
    for scan in scans:
        scan.getData()


#**************************************************************************

if __name__ == "__main__":
    main()


########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $HeadURL$
# $Id$
########### SVN repository information ###################
