import os
from pathlib import Path
from glob import glob
import subprocess

def createMosaic(pathInput,nombre,pathTmp,pathOutput):    
    mosaicos = ''

    for path in Path(pathInput).rglob('*harmonized_clip.tif'):
        #print(path, type(path))
        mosaicos += str(path) + ' '    

    nomMosaicTif = pathOutput+'planet_'+nombre+'.tif'
    print(nomMosaicTif)

    # Mosaico con fecha
    os.system('gdal_merge.py -n nan -o '+pathTmp+nombre+'_tmp.tif '+mosaicos)
    # Optimiza el geotiff
    os.system('gdal_translate -CO "TILED=YES" -CO "BLOCKXSIZE=512" -CO "BLOCKYSIZE=512" -CO "BIGTIFF=YES" '+pathTmp+nombre+'_tmp.tif '+nomMosaicTif)
    os.system('gdaladdo -r average '+nomMosaicTif+' 2 4 8 16 32')

def createMosaicSts(pathInput, nombre, pathTmp, pathOutput):
    mosaicos = ''

    for path in Path(pathInput).rglob('*harmonized_clip.tif'):
        mosaicos += str(path) + ' '    

    nomMosaicTif = os.path.join(pathOutput, f'planet_{nombre}.tif')
    print(nomMosaicTif)

    # Obtener el primer archivo del mosaico con glob
    first_image = glob(os.path.join(pathInput, '*harmonized_clip.tif'))[0]

    # Mosaico con fecha
    comando_merge = f"gdal_merge.py -n 0 -a_nodata 0 -init 0 -o {os.path.join(pathTmp, nombre)}_tmp.tif {mosaicos}"
    os.system(comando_merge)

    # Optimiza el geotiff
    comando_translate = f'gdal_translate -co "TILED=YES" -co "BLOCKXSIZE=512" -co "BLOCKYSIZE=512" -co "BIGTIFF=YES" {os.path.join(pathTmp, nombre)}_tmp.tif {nomMosaicTif}'
    os.system(comando_translate)

    # Agregar pirámides
    comando_addo = f'gdaladdo -r average {nomMosaicTif} 2 4 8 16 32'
    os.system(comando_addo)

    # Extraer y conservar estadísticas del primer archivo, genera el archivo con os.system y luego lo lee con subprocess
    comando_stats = f'gdalinfo -stats {first_image}'
    os.system(f'{comando_stats} > {os.path.join(pathTmp, nombre)}_stats.txt')

    with open(f'{os.path.join(pathTmp, nombre)}_stats.txt', 'r') as f:
        first_image_stats = f.read()

    
    # Buscar valores de mínimo y máximo en las estadísticas
    min_vals = []
    max_vals = []

    for line in first_image_stats.split('\n'):
        if 'STATISTICS_MINIMUM=' in line:
            min_vals.append(line.split('=')[-1])
        elif 'STATISTICS_MAXIMUM=' in line:
            max_vals.append(line.split('=')[-1])
    
    # Usar gdal_edit.py para establecer estos valores en el mosaico final
    for i, (min_val, max_val) in enumerate(zip(min_vals, max_vals)):
        band = i + 1
        comando_edit = f'gdal_edit.py -b {band} -stats {nomMosaicTif} -mo "STATISTICS_MINIMUM={min_val}" -mo "STATISTICS_MAXIMUM={max_val}"'
        os.system(comando_edit)

    # Borra el archivo temporal
    os.system(f'rm {os.path.join(pathTmp, nombre)}_tmp.tif')
    os.system(f'rm {os.path.join(pathTmp, nombre)}_stats.txt')

years = ['2019', '2020', '2021', '2022', '2023']

pathInputPlanet = '/datawork/AOD_average/input/planet_images/'
pathOutput = '/datawork/AOD_average/output/mosaics/'
pathTmp = '/datawork/AOD_average/tmp/'  

for year in years:
    print(year)
    pathOutput = '/datawork/AOD_average/output/mosaics/'+year+'/'
    # Lista las carpetas de los meses
    listMonths = glob(pathInputPlanet+year+'/*')
    for month in listMonths:
        # Se obtiene el nombre del mes
        monthName = month.split('/')[-1]
        # Se pasa el nombre del mes a minusculas
        monthName = monthName.lower()
        print(monthName)
        # Se enlistas los archivos de la carpeta de cada mes
        listFiles = glob(month+'/*harmonized_clip.tif')

        # Se crea el mosaico
        #createMosaic(month,monthName,pathTmp,pathOutput)
        createMosaicSts(month, monthName, pathTmp, pathOutput)
