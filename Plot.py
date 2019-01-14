import sys
from numpy import ndarray
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import math
import csv
import numpy as np
import scipy.interpolate
from matplotlib.mlab import griddata

from numpy import genfromtxt

name = '../WindPotentialScala/potential_pvpoly_1.0'
# sf_wind, wind100m, cf_wind_100m, wi_eroi5, wi_eroi12
index = 2

def main():
    plotData(name,index, output="eroimin_poly_8", xLabel="", show=True)
    print "Hello"
    
def plotData(csvFile, index, output, xLabel="", show=True):
    
    data = genfromtxt(csvFile, delimiter='\t', dtype=None)
     #### data preparation 
    lats = data[:, 0] 
    # # lon => x 
    lons = data[:, 1] 
    
    # # values => z 
    values = data[:, index]
    print "Size :", len(lats)
    print "Lat Min :", min(lats), "Lat Max :", max(lats)
    print "Lon Min :", min(lons), "Lon Max :", max(lons)
    #### later in the defined map 
    map = Basemap(projection='cyl', llcrnrlat=min(lats), urcrnrlat=max(lats), llcrnrlon=min(lons), urcrnrlon=max(lons), resolution='l')
    
    map.drawcoastlines()
    map.drawstates()
    map.drawcountries()
    # map.drawlsmask(land_color='coral',ocean_color='blue') 
    print "Maximum ", max(values), " - Minimum ", min(values)
    cs = map.contourf(lons, lats, values, np.linspace(#1.0, 3.0, 3
                                                      min(values)+0.01, max(values)+0.01, 250
                                                      , endpoint=False), tri=True ) #, latlon=True)
    cbar = map.colorbar(cs, location='bottom', pad="5%")
    #cbar.set_label(xLabel)
    #cbar.set_ticks(np.arange(0,100,5))
    
    if show: 
        plt.show()
    else :
        # High resolution
        plt.savefig(output + '.pdf', dpi=250, bbox_inches='tight')
        plt.savefig(output + '.png', dpi=250, bbox_inches='tight')
        plt.close()
        
    return

if __name__ == "__main__":
    sys.exit(main())
