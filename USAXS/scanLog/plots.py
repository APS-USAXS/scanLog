#!/usr/bin/env python

'''make plots of the last *n* scans in the scanlog'''


import glob
import os
import spec2nexus.spec
import xmlSupport


###########
###########  THIS MODULE IS BEING DEVELOPED
###########  IT IS NOT READY FOR PRODUCTION USE
###########


SCANLOG = '/share1/local_livedata/scanlog.xml'


class Scan(object):
    
    def __init__(self, title, data_file, scan_type, scan_number, scan_id):
        self.title = title
        self.scan_type = scan_type
        self.data_file = data_file
        self.scan_number = int(scan_number)
        self.scan_id = scan_id
        self.spec_scan = None
        # TODO: make a safe ID, suitable for use as an HDF5 label (<63 char, none odd)
        self.Q = None
        self.I = None
    
    def __str__(self, *args, **kwargs):
        return self.scan_type + ": " + self.title
    
    def getSpecScan(self):
        if self.spec_scan is None:
            # TODO: use cache of SpecDataFile objects
            spec = spec2nexus.spec.SpecDataFile(self.data_file)
            self.spec_scan = spec.getScan(self.scan_number)
        return self.spec_scan

    def getData(self):
        if self.scan_type in ('uascan', 'sbuascan'):
            # TODO: implement a cache of already reduced data
            if self.spec_scan is None:
                self.getSpecScan()
            # TODO: need to reduce the USAXS raw data
            print self.spec_scan.scanCmd
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
            specfile = scan.find('file').text.strip()
            specfiledir = os.path.dirname(specfile)
            
            # get the HDF5 file name from the SPEC file (no search needed)
            spec = spec2nexus.spec.SpecDataFile(specfile)
            spec_scan = spec.getScan(int(scan.attrib['number']))
            for line in spec_scan.comments:
                if line.find('FlyScan file name = ') > 1:
                    hdf5_file = line.split('=')[-1].strip().rstrip('.')
                    hdf5_file = os.path.abspath(os.path.join(specfiledir, hdf5_file))
                    if os.path.exists(hdf5_file):
                        # actual data file
                        scan.data_file = hdf5_file
                        ok = True
                    break

    return ok


def last_n_scans(xml_log_file, number_scans):
    xml_doc = xmlSupport.openScanLogFile(SCANLOG)

    scans = []
    for scan in reversed(xml_doc.findall('scan')):
        if ok_to_plot(scan):
            scans.append(scan)
            if len(scans) == number_scans:
                break
    return reversed(scans)


def main():
    scans = [Scan(scan.find('title').text.strip(),
                 scan.find('file').text.strip(),
                 scan.attrib['type'],
                 scan.attrib['number'],
                 scan.attrib['id'],
             ) for scan in last_n_scans(SCANLOG, 5)]
    print '\n'.join(['%s     %s' % (_.scan_id, str(_)) for _ in scans])
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
