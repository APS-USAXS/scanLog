#!/usr/bin/env python

'''demo use of MatPlotLib for the USAXS livedata plots'''


import datetime
import matplotlib.pyplot as plt
import numpy as np

BISQUE_RGB    = (255./255, 228./255, 196./255)  # 255 228 196 bisque
MINTCREAM_RGB = (245./255, 255./255, 250./255)  # 245 255 250 MintCream

SYMBOL_LIST = ("^", "D", "s", "v", "<", ">")
COLOR_LIST = ("green", "purple", "blue", "black", "orange") # red is NOT in the list

CHART_FILE = 'livedata.png'


class Plottable_USAXS_Dataset(object):
    Q = None
    I = None
    label = None


def livedata_plot(datasets, plotfile):
    '''
    generate the USAXS livedata plot
    
    :param [Plottable_USAXS_Dataset] datasets: USAXS data to be plotted, newest data last
    :param str plotfile: file name to write plot image
    '''
    fig = plt.figure(figsize=(7.5, 8), dpi=300)

    ax = fig.add_subplot('111', axisbg=MINTCREAM_RGB)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'$|Q|, 1/\AA$')
    ax.set_ylabel(r'Raw Intensity ($I$), a.u.')
    ax.grid(True, which='both')

    for i, ds in enumerate(datasets):
        if i < len(datasets)-1:
            color = COLOR_LIST[i % len(COLOR_LIST)]
            symbol = SYMBOL_LIST[i % len(SYMBOL_LIST)]
        else:
            color = 'red'
            symbol = 'o'
        ax.plot(ds.Q, ds.I, symbol, label=ds.label, mfc='w', mec=color, ms=3, mew=1)

    title = 'APS/XSD USAXS: ' + str(datetime.datetime.now())
    plt.title(title, fontsize=12)
    plt.legend(loc='lower left', fontsize=10)   # FIXME: plots two symbols for each dataset
    plt.savefig(plotfile, bbox_inches='tight', facecolor=BISQUE_RGB)


def main():
    x = np.arange(0.105, 2*np.pi, 0.01)
    ds1 = Plottable_USAXS_Dataset()
    ds1.Q = x
    ds1.I = np.sin(x**2) * np.exp(-x) + 1.0e-5
    ds1.label = 'sin(x^2) exp(-x)'
    
    ds2 = Plottable_USAXS_Dataset()
    ds2.Q = x
    ds2.I = ds1.I**2 + 1.0e-5
    ds2.label = '$[\sin(x^2)\cdot\exp(-x)]^2$'
    
    ds3 = Plottable_USAXS_Dataset()
    ds3.Q = x
    ds3.I = np.sin(5*x) / (5*x)  + 1.0e-5
    ds3.label = 'sin(5x)/(5x)'
    
    ds4 = Plottable_USAXS_Dataset()
    ds4.Q = x
    ds4.I = ds3.I**2 + 1.0e-5
    ds4.label = r'$[\sin(5x)/(5x)]^2$'
    
    livedata_plot([ds2, ds4], CHART_FILE)


#**************************************************************************

if __name__ == "__main__":
    main()


########### SVN repository information ###################
# $Date: 2015-02-06 13:26:31 -0600 (Fri, 06 Feb 2015) $
# $Author: jemian $
# $Revision: 1176 $
# $HeadURL: https://subversion.xray.aps.anl.gov/small_angle/USAXS/scanLog/plots.py $
# $Id$
########### SVN repository information ###################
