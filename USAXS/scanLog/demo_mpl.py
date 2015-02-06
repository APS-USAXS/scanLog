#!/usr/bin/env python

'''demo use of MatPlotLib for the USAXS livedata plots'''


import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
#mpl.rcParams['text.usetex'] = True
import numpy as np


class Dataset(object):
    x = None
    y = None
    label = None


def plot_data(datasets, title, plotfile):
    fig = plt.figure()
    # TODO: set backgrond outside plot frame to bisque
    bisque_rgb = (255./255, 228./255, 196./255)  # 255 228 196 bisque
    mintcream_rgb = (245./255, 255./255, 250./255)  # 245 255 250 MintCream
    ax = fig.add_subplot('111', axisbg=mintcream_rgb)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'$|Q|, 1/\AA$')
    ax.set_ylabel(r'$I$, a.u.')
    ax.grid(True)
    for ds in datasets:
        ax.plot(ds.x, ds.y, label=ds.label)
    plt.title(title)
    plt.legend(loc='lower left', prop=font_manager.FontProperties(size=10))
    plt.savefig(plotfile, bbox_inches='tight')


def main():
    x = np.arange(0.105, 2*np.pi, 0.01)
    ds1 = Dataset()
    ds1.x = x
    ds1.y = np.sin(x**2) * np.exp(-x)
    ds1.label = 'sin(x^2) exp(-x)'
    
    ds2 = Dataset()
    ds2.x = x
    ds2.y = ds1.y**2
    ds2.label = '$[\sin(x^2)\cdot\exp(-x)]^2$'
    
    ds3 = Dataset()
    ds3.x = x
    ds3.y = np.sin(5*x) / (5*x)
    ds3.label = 'sin(5x)/(5x)'
    
    ds4 = Dataset()
    ds4.x = x
    ds4.y = (np.sin(5*x) / (5*x))**2
    ds4.label = r'$[\sin(5x)/(5x)]^2$'
    
    plot_data([ds2, ds4], 'Something wonderful', 'demo_mpl.png')


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
