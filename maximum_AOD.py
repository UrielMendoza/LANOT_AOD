'''
Script to calculate the maximum GOES-6 ABI AOD for day and month

@author: urielm
@date: 2024-02-14
'''

from glob import glob
import os
import numpy as np
#from netCDF4 import Dataset
import matplotlib.pyplot as plt
import rasterio
import datetime
from osgeo import gdal, osr

def creaTif(dsRef,npy,output):
    geotransform = dsRef.GetGeoTransform()
    nx = dsRef.RasterXSize
    ny = dsRef.RasterYSize
    dst_ds = gdal.GetDriverByName('GTiff').Create(output, ny, nx, 1, gdal.GDT_Float32)
    dst_ds.SetGeoTransform(geotransform)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(dsRef.GetProjectionRef())
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds.GetRasterBand(1).WriteArray(npy)
    dst_ds.FlushCache()
    dst_ds = None

def obtainDate(file):
    date = file.split('/')[-1].split('_')[4]
    date = datetime.datetime.strptime(date, 's%Y%m%d')
    time = file.split('/')[-1].split('_')[7]
    time = datetime.datetime.strptime(time, '%H%MUTC')
    # Add the time to the date
    date = date.replace(hour=time.hour, minute=time.minute)
    return date

def obtainDateMonth(file):
    #CG_ABI-L2-AODC-avr-M6_G16_2023132.tif
    date = file.split('/')[-1].split('_')[3].split('.')[0]
    date = datetime.datetime.strptime(date, '%Y%j')
    return date

def filesDays(files):    
    filesDays = {}
    days = []
    # Loop for obtain sublists of files from a same day
    print('Obtaining sublists of files from a same day... ')
    for file in files:
        date1 = obtainDate(file)
        # Julian day
        day1 = date1.strftime('%j')
        try:
            date2 = obtainDate(files[files.index(file) + 1])
        except IndexError:
            return filesDays
        day2 = date2.strftime('%j')
        # If the next day is the same, append the file to the list
        if day1 == day2:
            days.append(file)
        # If the next day is different, append the file to the list and return the list
        else:
            print('Day: ', day1)
            print('Number of files: ', len(days))
            days.append(file)
            filesDays[day1] = days
            days = []
    return filesDays

def filesMonths(files):
    filesMonths = {}
    months = []
    # Loop for obtain sublists of files from a same month
    print('Obtaining sublists of files from a same month... ')
    for file in files:
        date1 = obtainDateMonth(file)
        # Month
        month1 = date1.strftime('%m')
        try:
            date2 = obtainDateMonth(files[files.index(file) + 1])
            month2 = date2.strftime('%m')
        except IndexError:
            # When we've reached the last file, add the current month's files to the dictionary
            months.append(file)
            filesMonths[month1] = months
            return filesMonths
        # If the next month is the same, append the file to the list
        if month1 == month2:
            months.append(file)
        # If the next month is different, append the file to the list and return the list
        else:
            print('Month: ', month1)
            print('Number of files: ', len(months))
            months.append(file)
            filesMonths[month1] = months
            months = []
    return filesMonths

def main(interval, year):
    if interval == 'day':
        pathInput = '/data/tmp/AOD_average/geotiff/'
    elif interval == 'month':
        pathInput = '/data/tmp/AOD_average/maximum/day/' + year + '/geotiff/'
    elif interval == 'year':
        pathInput = '/data/tmp/AOD_average/maximum/month/' + year + '/geotiff/'
    pathOutput = '/data/tmp/AOD_average/maximum/'
    pathTmp = '/data/tmp/AOD_average/tmp/'
    pathRef = '/home/urielm/AOD_average/data/ref/ref_AOD.tif'
    # Open the reference file
    ref = './data/ref/ref_AOD.tif'

    # List all files in the input directory
    if interval == 'day':
        files = glob(pathInput + year + '/*.tif')
    elif interval == 'month':
        files = glob(pathInput + '*.tif')
    elif interval == 'year':
        files = glob(pathInput + '*.tif')
    files.sort()

    if interval == 'day':
        # Obtain the files from a same day
        filesDate = filesDays(files)
    elif interval == 'month':
        # Obtain the files from a same month
        filesDate = filesMonths(files)
    elif interval == 'year':
        filesDate = {}
        filesDate[year] = files

    # Loop over files from a same day
    print('Processing files... ')
    for date in filesDate:
        # Variable to save the number of files
        num_files = 0
        # Variable to save the sum of AOD
        f = 97
        c = 118
        # Create a numpy array boolean with the same size as the AOD
        aod_numpix = np.zeros((f,c))
        # Create a numpy array with the same size as the AOD to save the maximum AOD
        aod_max = np.zeros((f,c))

        if interval == 'day':
            print('Day: ', date)
        elif interval == 'month':
            print('Month: ', date)
        elif interval == 'year':
            print('Year: ', date)

        for file in filesDate[date]:
            print('Processing file: ', file)
            # Open the file geotiff with rasterio
            with rasterio.open(file) as src:
                aod = src.read(1)

            # Print the shape of the AOD
            #print('Shape: ', aod.shape)
            #print('Type: ', aod.dtype)
            #print('Min: ', np.nanmin(aod))
            #print('Max: ', np.nanmax(aod))

            if interval == 'day':
                # Change the type of the AOD to float
                aod = aod.astype(float)

                # Obtain the fill value with rasterio
                #fill_value = src.nodatavals[0]
                fill_value = -32768.0
                    
                # Change the fill value to NaN
                aod[aod == fill_value] = np.nan

                # Obtain the scale factor and with rasterio
                #scale_factor = src.descriptions[0]
                #scale_factor = 9.1555528e-05

                # Obtain the offset with rasterio
                #add_offset = src.descriptions[1]
                #add_offset = 2.0

                # Apply the scale factor and offset
                #aod = (aod * scale_factor) + add_offset
                #print(aod)

                # Assign the maximum AOD to the current AOD
                #aod_max = aod

            # Filter values from 0 to 1
            #aod[aod < 0] = np.nan
            #aod[aod > 1] = np.nan

            # If the pixel is not NaN, sum 1 to the number of pixels
            aod_numpix += ~np.isnan(aod)
            #print(aod_numpix)

            # Interate each pixel to compare the maximum AOD with the previous maximum AOD
            for i in range(f):
                for j in range(c):
                    if not np.isnan(aod[i,j]):
                        if aod[i,j] > aod_max[i,j]:
                            aod_max[i,j] = aod[i,j]
            
            
            #print(aod_sum)
            num_files += 1     

        print('Number of files: ', num_files)

        # Calculate the maximum AOD with the sum and the number of pixels
        #aod_avg = aod_sum / aod_numpix

        # Normalize the maximum AOD to the range 0-1
        #aod_avg = (aod_avg - np.nanmin(aod_avg)) / (np.nanmax(aod_avg) - np.nanmin(aod_avg))

        # Plot the number of pixels without NaN
        #plt.imshow(aod_numpix)
        #plt.show()
        # Plot the sum of AOD
        #plt.imshow(aod_sum)
        #plt.show()
        # Plot the maximum AOD with the range : -0.05 to +5.00.
        plt.imshow(aod_max, vmin=-0.05, vmax=5.00)
        # Add colorbar adjusted to the range of AOD values 
        plt.colorbar()
        #plt.show()
        # Add title
        if interval == 'day' or interval == 'month':
            plt.title('Maximum AOD ' + year + ' ' + date)
        elif interval == 'year':
            plt.title('Maximum AOD ' + year)
        if interval == 'day':
            filename = pathOutput + 'day/' + year + '/png/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + date + '.png'
        elif interval == 'month':
            filename = pathOutput + 'month/' + year + '/png/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + date + '.png'
        elif interval == 'year':
            filename = pathOutput + 'year/' + year + '/png/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + '.png'
        plt.savefig(filename)
        plt.close()

        # Save the maximum AOD to a GeoTIFF file with rasterio
        # Obtain the crs and transform
        with rasterio.open(ref) as src:
            crs = src.crs
            transform = src.transform
        if interval == 'day':
            filename = pathOutput + 'day/' + year + '/geotiff/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + date + '.tif'
        elif interval == 'month':
            filename = pathOutput + 'month/' + year + '/geotiff/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + date + '.tif'
        elif interval == 'year':
            filename = pathOutput + 'year/' + year + '/geotiff/' + 'CG_ABI-L2-AODC-max-M6_G16_' + year + '.tif'
        with rasterio.open(filename, 'w', driver='GTiff', height=f, width=c, count=1,
        dtype=aod_max.dtype, crs=crs, transform=transform) as dst:
            dst.write(aod_max, 1)
            
        

if __name__ == "__main__":
    dates = ['day', 'month', 'year']
    years = ['2018', '2019', '2020', '2021', '2022', '2023']
    for date in dates:
        for year in years:
            main(date, year)

