'''
Script to cut region from GOES-6 ABI AOD

@author: urielm
@date: 2024-02-14
'''

from glob import glob
import os
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import datetime
import geopandas as gpd
import rasterio
#import pyproj
#from osgeo import gdal, osr

pathInput = '/data/tmp/AOD_average/netcdf/2020/'
pathOutput = '/data/tmp/AOD_average/geotiff/2020/'
pathTmp = '/data/tmp/AOD_average/tmp/'
pathRegion = '/home/urielm/AOD_average/data/region/Municipios/Municipios_MM.shp'
pathRef = '/home/urielm/AOD_average/data/ref/ref_AOD.tif'

def createTif(npy, pathRef, pathOutput, filename):
    f = 1500
    c = 2500
    # Obtain the crs and transform
    with rasterio.open(pathRef) as src:
        crs = src.crs
        transform = src.transform
    filename = pathOutput + filename
    with rasterio.open(filename, 'w', driver='GTiff', height=f, width=c, count=1,
    dtype=npy.dtype, crs=crs, transform=transform) as dst:
        dst.write(npy, 1)

# Region to cut
# Open the file region with geopandas
region = gpd.read_file(pathRegion)
# Reproject to UTM 14N
region = region.to_crs('EPSG:32614')
# Obtain the bounding box
bbox = region.total_bounds
# Reproject to UTM
print('Bounding box: ', bbox)
# Define the variable to process
var = 'AOD'

# List all files in the input directory
files = glob(pathInput + '*.nc')
files.sort()

# Loop over all files
print('Processing files... ')
for file in files:    
    #print("Processing file: ", file)
    # Obtain the date from the file name from this format "s20203632156180"
    date = file.split('/')[-1].split('_')[3]
    date = date[:-2]
    date = datetime.datetime.strptime(date, 's%Y%j%H%M%S')

    # Filter date to range  12:00 - 24:00 
    if date.hour < 12:
        continue
    else:
        print("Date: ", date)
        
        # Obtain name 
        name = file.split('/')[-1].split('.')[0]+'.tif'

        # Open the file
        #nc = Dataset(file, 'r')
        # Read the AOD variable
        #aod = nc.variables['AOD'][:].data
        # Obtain the fill value
        #fill_value = nc.variables['AOD']._FillValue
        # Change the fill value to NaN
        #aod[aod == fill_value] = np.nan
        # Obtain the scale factor and offset
        #scale_factor = nc.variables['AOD'].scale_factor
        #add_offset = nc.variables['AOD'].add_offset
        # Apply the scale factor and offset
        #aod = aod * scale_factor + add_offset

        # Convert the NetCDF to geotiff with GDAL
        os.system('gdal_translate -of GTiff NETCDF:"'+file+'":'+var+' '+pathTmp+'AOD.tif')

        # Convert the NetCDF to geotiff with rasterio
        #createTif(aod, pathRef, pathTmp, 'AOD.tif')

        # Reproyect to EPSG:32614
        os.system('gdalwarp -t_srs EPSG:32614 '+pathTmp+'AOD.tif '+pathTmp+'AOD_32614.tif')

        # Cut the region with gdalwarp
        os.system('gdalwarp -te '+str(bbox[0])+' '+str(bbox[1])+' '+str(bbox[2])+' '+str(bbox[3])+' '+pathTmp+'AOD_32614.tif '+pathOutput+name)







