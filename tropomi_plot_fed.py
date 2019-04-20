#!/usr/bin/env python
import os, sys, re
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from pylab import *
from numpy import *
#from Scientific.IO.NetCDF import *
import netCDF4
from matplotlib.collections import PolyCollection
import matplotlib.colors as colors
import matplotlib.cm as cmx
import numexpr


#################### Code to plot TROPOMI data #######################



USE_NETCDF4 = True

def prepare_geo(var, latb, lonb, selection="both"):
    if latb.shape[0] == 1:
        dest_shape = (latb.shape[1]+1, latb.shape[2]+1)
    else:
        dest_shape = (latb.shape[0]+1, latb.shape[1]+1)
    
    dest_lat = np.zeros(dest_shape, dtype=np.float64)
    dest_lon = np.zeros(dest_shape, dtype=np.float64)
    
    
    if latb.shape[0] == 1:
        dest_lat[0:-1, 0:-1] = latb[0, :, :, 0]
        dest_lon[0:-1, 0:-1] = lonb[0, :, :, 0]
        dest_lat[-1, 0:-1] = latb[0, -1, :, 3]
        dest_lon[-1, 0:-1] = lonb[0, -1, :, 3]
        dest_lat[0:-1, -1] = latb[0, :, -1, 1]
        dest_lon[0:-1, -1] = lonb[0, :, -1, 1]
        dest_lat[-1, -1] = latb[0, -1, -1, 2]
        dest_lon[-1, -1] = lonb[0, -1, -1, 2]
    else:
        dest_lat[0:-1, 0:-1] = latb[:, :, 0]
        dest_lon[0:-1, 0:-1] = lonb[:, :, 0]
        dest_lat[-1, 0:-1] = latb[-1, :, 3]
        dest_lon[-1, 0:-1] = lonb[-1, :, 3]
        dest_lat[0:-1, -1] = latb[:, -1, 1]
        dest_lon[0:-1, -1] = lonb[:, -1, 1]
        dest_lat[-1, -1] = latb[-1, -1, 2]
        dest_lon[-1, -1] = lonb[-1, -1, 2]
    
    boolarray = np.logical_or((dest_lon[0:-1, 0:-1]*dest_lon[1:, 0:-1]) < -100.0, 
                              (dest_lon[0:-1, 0:-1]*dest_lon[0:-1, 1:]) < -100.0)
    

    dest_lon[0:-1, 0:-1] = np.where(boolarray, 2e20, dest_lon[0:-1, 0:-1])
    print 'Shape of variable: ',var.shape
    if var.shape[0] == 1:
        var = var[0, ...]
    else:
        var = var[...]


    return var, dest_lat, dest_lon

def find_var_recursively(grp, varname):
    if varname in grp.variables.keys():
        return grp.variables[varname]
                
    grp_list = grp.groups.keys()
    for grp_name in grp_list:
        rval = find_var_recursively(grp.groups[grp_name], varname)
        if rval is not None:
            return rval
    
    return None


def get_data(f, field, filters):
    ref = netCDF4.Dataset(f, 'r')
    lonb =  find_var_recursively(ref, 'longitude_bounds')
    latb =  find_var_recursively(ref, 'latitude_bounds')
    var = find_var_recursively(ref,field)
    
    try:
        extended_name = var.long_name
    except AttributeError:
        try:
            extended_name = var.standard_name
        except AttributeError:
            extended_name = field.replace('_', ' ')
    try:
        unit = var.units
    except AttributeError:
        unit = ""
    if unit == "1":
        unit = ""
        
    try:
        fill_value = var._FillValue
    except:
        fill_value = float.fromhex('1.ep122')
    xtrack_range = None    
    if xtrack_range is not None:
        var = var[..., xtrack_range[0]:xtrack_range[1]]
    else:
        var = var[...]
        
    var = np.where(var>=fill_value, np.nan, var)
    #Filter for negative values 
    #var = np.where(var<0.,np.nan,var)
    #This factor is to convert mol/m2 to molec/cm2    
    factor = 6.02214E19
    #factor = None
    if factor is not None:
        var = var*factor
        unit = 'molec/cm2'
    
    if filters is not None:
            for fltr in filters:
                try:
                    m = re.match('^(.+) ?(<|>|!=|==) ?(.+)$', fltr)
                except:
                    print("Error in filter '{0}', regex invalid".format(fltr))
                    continue
                if m is None:
                    print("Error in filter '{0}', regex did not match".format(fltr))
                    continue
                
                items = m.groups()
                name = items[0].strip()
                
                try:
                    filtervar = find_var_recursively(ref, name)
                except:
                    print("Error in filter '{0}', error accessing netCDF file".format(fltr))
                    continue
                if filtervar is None:
                    print("Error in filter '{0}', variable not found".format(fltr))
                    continue
                
                if xtrack_range is not None:
                    filtervar = filtervar[..., xtrack_range[0]:xtrack_range[1]]
                else:
                    filtervar = filtervar[...]
                
                lst = ["filtervar"]
                lst.extend(items[1:])
                ex = " ".join(lst)
                
                try:
                    idx = numexpr.evaluate(ex)
                except (KeyError, NotImplementedError, SyntaxError):
                    print("Error in filter '{0}', expression invalid".format(fltr))
                    continue
                
                var = np.where(idx, var, np.nan)

    var,latb,lonb = prepare_geo(var,latb,lonb)
    
    return var,latb,lonb,extended_name, unit

latlon_Europe = [[30.0, 58.0],
                 [-15.0,20.0]]
latlon_World = [[-60.0, 75.0],
                 [-180.,180.0]]
latlon_Paris = [[44.0,58.447],
               [-10.0,18.0]]
corners = latlon_World

def plot_variable(file_list,variable2plot):
    map = Basemap(projection='merc',llcrnrlat=corners[0][0],urcrnrlat=corners[0][1],
    llcrnrlon=corners[1][0],urcrnrlon=corners[1][1],resolution='l')   #Paris: lat = 48.5 - 52, lon = 1 - 4.5

#59 , -10
#44 , 18

    # draw coastlines, country boundaries, fill continents.
    map.drawcoastlines(linewidth=0.6, color = 'black')
    map.drawcountries(linewidth = 0.6, color = 'black')
   
    map.drawlsmask(ocean_color='white') #optional parameter: land_color='white'
    

    # draw lat/lon grid lines every x degrees.
    map.drawparallels(np.arange( -90.,90.,10.),linewidth=0.1,color = 'Black',labels=[1,0,0,0])
    map.drawmeridians(np.arange(-180.,180.,20.),linewidth=0.1,color = 'Black',labels=[0,0,0,1])
   
    cmap = cm.get_cmap(name='rainbow')   #NO2: 'rainbow'   clouds: 'Blues_r'
    cmap.set_under('white')
    #cmap.set_under('0.3')
    #cmap.set_over('1.0')

    data_range = None
    dynamic_range = False
    if data_range is None:
        data_range = [1e20, -1e20]
        dynamic_range = True

    filters = [
               'cloud_radiance_fraction_nitrogendioxide_window < 0.5',
               'surface_albedo < 0.3',
               'air_mass_factor_troposphere > 0.2'
               ]

    data = []

    for f in file_list:    
        var,latb,lonb,extended_name, unit = get_data(f,variable2plot,filters) 

        xtrack_range = None
    
        if dynamic_range:
            try:
                sel_data = var.data[np.logical_not(var.mask)]
                if sel_data.shape[0] == 0:
                    print 'continue in the loop'
            except AttributeError:
                sel_data = var            
        
            data_range[0] = min(np.nanmin(sel_data), data_range[0])
            data_range[1] = max(np.nanmax(sel_data), data_range[1])

        data.append((var, latb, lonb))
    for var, latb, lonb in data:
        x,y = map(lonb,latb)
        if xtrack_range is None:
            #cs = map.pcolor(x,y,var,cmap=cmap,latlon=False,vmin=0, vmax=15)  #comment this special range out later
            cs = map.pcolor(x,y,var,cmap=cmap,latlon=False,vmin=0, vmax=10e15)  #-10e15, vmax=20e15  #SET RANGE HERE
        else:
                # pcolormesh
            cs = map.pcolor(x[:,:],
                            y[:,:],
                            var[:,:],
                            cmap=cmap,
                            latlon=False, 
                            vmin=data_range[0], vmax=data_range[1])

    cbar = map.colorbar(cs,location='right',pad="12%", extend="both")
    cbar.set_label(unit)
    
    map.drawlsmask(land_color='white')
    
    # Label for the plot
    label = 'TROPOMI o00569 - 11-22-2017'
    #if label is None:
     #   plt.title(extended_name)
    #else:
        #plt.title("{0} - {1}".format(extended_name,label))
    
    # Name of the file for figure
    fig = 'paris_1122_tropomi'
    if fig is None:
        plt.show()
    else:
        f = plt.gcf()
        f.set_size_inches(10.0, 6.0, forward=True)
        plt.savefig(fig, dpi=300)
        plt.show()

if __name__ == "__main__":
# Path to file storage in CapeGrim
    path1 = '/home/WUR/batti002/test_ride/'

    #F1 = path1 + 'S5P_NRTI_L2__NO2____20190326T114331_20190326T114831_07506_01_010202_20190326T121957.nc'
    
    #Repro files june 2018
    
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180610T110109_20180610T124437_03406_01_010202_20190208T122356.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180611T122337_20180611T140705_03421_01_010202_20190208T155926.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180612T120435_20180612T134803_03435_01_010202_20190208T204140.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180613T114533_20180613T132900_03449_01_010202_20190208T235133.nc'
    #Repro files august 2018
    #europe
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180803T104729_20180803T123037_04172_01_010202_20190216T142505.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180804T102837_20180804T121132_04186_01_010202_20190216T193101.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180805T115028_20180805T130003_04201_01_010202_20190216T205754.nc'
    #F1 = path1 + 'S5P_RPRO_L2__NO2____20180806T113138_20180806T131450_04215_01_010202_20190216T222812.nc'
    
    #asia
    #F2 = path1 + 'S5P_RPRO_L2__NO2____20180805T050429_20180805T064757_04197_01_010202_20190216T201123.nc'
    
    #experiment: combine two parts of european sea
    F1 = path1 + 'S5P_RPRO_L2__NO2____20180806T094952_20180806T113320_04214_01_010202_20190216T222121.nc'
    F2 = path1 + 'S5P_RPRO_L2__NO2____20180806T131252_20180806T145619_04216_01_010202_20190217T010134.nc'
    F3 = path1 + 'S5P_RPRO_L2__NO2____20180806T113138_20180806T131450_04215_01_010202_20190216T222812.nc'
    
    file_list = [F1]
    
    variable2plot = 'nitrogendioxide_tropospheric_column'
    #variable2plot = 'surface_classification'
    #variable2plot = 'cloud_radiance_fraction_nitrogendioxide_window'
    plot_variable(file_list,variable2plot)

