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

name = '../WindPotential/world_c_k'
# 4 = wind at 10 metres, 5 = wind at 80 metres onshore and 90 metres offshore
index = 7

def main():
    plotData(name, index)

def plotData(csvFile, index):
    data = genfromtxt(csvFile, delimiter='\t', dtype=None)
    # data = genfromtxt(csvFile, delimiter='\t', dtype=None)
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
    cs = map.contourf(lons, lats, values, np.linspace(min(values)+0.01, max(values)+0.01
                                                      , 2, endpoint=True), tri=True ) #, latlon=True)
    cbar = map.colorbar(cs, location='bottom', pad="5%")
    #cbar.set_label('Mean Wind Speed at 125 m [m/s]')
    #cbar.set_ticks(np.linspace(0, 15, 7))
    #plt.savefig('wind125m' + '.png', dpi=250, bbox_inches='tight')
    plt.show()
    # return

if __name__ == "__main__":
    sys.exit(main())
