#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed 29 Jul 2020 04:00:38 PM CDT

@author: Alejandro Aguilar Sierra, asierra@unam.mx 
Laboratorio Nacional de Observación de la Tierra, UNAM

Funciones para recuperar datos del GOES-16 almacenados en el servidor
lustre con base en intervalos de tiempo.

"""

import os
import re
import sys
import tarfile
from datetime import date


def horastr2minutos(hora):
    if not re.match("^\d{2}:\d{2}$", hora):
        print("Formato de hora incorrecto, debe ser HH:mm", hora)
        return None
    h, m = hora.split(':')
    mins = int(h)*60 + int(m)
    return mins

def horaint2minutos(hora):
    if hora < 0 or hora > 2400:
        print("Formato de hora incorrecto, debe ser entero entre 0 y 2400:", hora)
        return None
    h = hora // 100
    m = hora % 100
    mins = h*60 + int(m)
    return mins

def minutos2hora(minutos):   
    return "{}:{}".format(minutos//60, minutos % 60)
    
def fecha2juliandate(fecha):    
    r = re.match(r"^(\d{4})(\d{2})(\d{2})$", fecha)
    if not r:
        print("Error: Formato de fecha incorrecto, debe ser YYYYMMDD")
        return None    
    year, month, day = r.groups()
    d = date(int(year), int(month), int(day))
    jday = d.timetuple().tm_yday
    sdate = "{}{:03d}".format(year, jday)
    jdate = int(sdate)
    return jdate

def juliandates_range(jdate1, jdate2, days_step):
    return list(range(jdate1, jdate2, days_step))

def  hours_range(hora1, hora2, step):
     minslist = list(range(hora1, hora2+1, step))
     return minslist
 
def depot_goes_directory(sensor, nivel, dominio):    
    path = "/depot/goes16/{}/{}/{}".format(sensor, nivel, dominio)
    if os.path.isdir(path):
        return path
    else:
        print("Error: No se puede abrir el directorio", path)
        return None

def depot_goes_files_date(fecha, directorio):    
    if not isinstance(fecha, int):
        print("Error: La fecha debe ser un entero YYYYJJJ con 7 cifras")
        return None
    year = fecha//1000
    jday = fecha % 1000
    week = jday//7 + 1
    path = "{}/{}/{:02d}".format(directorio, year, week)
    print(year, jday, week, path)
    sfecha = "s{}".format(fecha)
    files = []
    if os.path.isdir(path):
        with os.scandir(path) as i:
            for entry in i:
                if entry.is_file():
                    if re.search(sfecha, entry.name):
                        files.append(path + "/" + entry.name)
    else:
        print("Error: No se puede abrir el directorio", path)
        return None
    return files

def depot_get_minutes_from_filename(filename):
    r = re.search("s\d{7}(\d{2})(\d{2})", filename)
    if r:
        h, m = r.groups()
        minutos = int(h)*60 + int(m)
        return minutos
    return None

def depot_goes_files_date_times(horas, fecha, directorio):    
    files = depot_goes_files_date(fecha, directorio)
    if not files or len(files) == 0:
        print("Aviso: No hay datos en la fecha", fecha)
        return None

    mins_min = horas[0]
    mins_max = horas[-1]
    
    hfiles = []
    minsf = []
    for f in files:
        r = re.search("s\d{7}(\d{2})(\d{2})", f)        
        if r:
            h, m = r.groups()
            mf = int(h)*60 + int(m)
            if mf >= mins_min and mf <= mins_max:
                hfiles.append(f)
                minsf.append(mf)

    if len(hfiles) == 0:
        print("Aviso: No hay datos entre las horas", minutos2hora(mins_min), minutos2hora(mins_max))
        return None
    
    if len(horas) > 2:
        hfiles2 = []
        for m in horas:
            mf = min(minsf, key=lambda x:abs(x-m))
            i = minsf.index(mf)
            hfiles2.append(hfiles[i])
        hfiles = hfiles2

    return hfiles

def depot_goes_extract(datafile, destdir):
    tarf = tarfile.open(datafile, "r")
    file = tarf.extractall(destdir)
    tarf.close()
    print(file)
    return True
    
def depot_goes_extract_products(datafile, products, destdir):
    try:
        count = 0
        print("Abriendo ", datafile)
        tar = tarfile.open(datafile, "r")
        for name in tar.getnames():
            for p in products:
                if re.search(p, name):
                    tar.extract(name, destdir)
                    count += 1                    
        tar.close()
        print(count, "archivos extraidos en", destdir)
        return True
    except KeyError:
        print("Error: {} no está en {}".format(filename, tarfilename))
        tar.close()
        return False
    except IOError:
        print("Error: No se pudo abrir", datafile)
        return False
    except tarfile.ReadError:
        print("Error: No es un archivo tar válido", datafile)
        return False

def error(msg):
    print("Error: ", msg)
    exit(1)
    
def recupera_datos(nivel, dominio, fechas, horas=None, sensor="abi"):
    if sensor != "abi":
        error("Sensor no reconocido "+sensor)
    if nivel != "l1b" and nivel != "l2":
        error("Nivel no reconocido "+nivel)
    if dominio != "fd" and dominio != "conus":
        error("Dominio no reconocido "+dominio)    

    directorio = depot_goes_directory(sensor, nivel, dominio)
    files = []
    for fe in fechas:
        # Si está en formato YYYYMMDD convierte a juliano
        if  isinstance(fe, str) and len(fe)==8:
            fecha = fecha2juliandate(fe)
        # Si tiene 7 cifras, asumimos que es juliano YYYYJJJ    
        elif  isinstance(fe, str) and len(fe)==7:
            fecha = int(fe)    
        elif  isinstance(fe, int) and fe < 10000000:
            fecha = fe
        else:
            error("Formato de fecha no reconocido: "+fe)            
        lista = depot_goes_files_date(fecha, directorio)
        files += lista

    minutes = []
    minutes_intervals = []
    if horas:
        # Procesa primero la lista de horas
        for t in horas:
            if isinstance(t, str) and len(t)==5:
                m = horastr2minutos(t)
            elif isinstance(t, int):
                m = horaint2minutos(t)
            # Intervalo
            elif isinstance(t, str) and len(t)==11:
                h1, h2 = t.split('-')                
                minutes_intervals.append((horastr2minutos(h1), horastr2minutos(h2)))
                continue
            else:
                error("Formato de hora no reconocido: "+t)
            minutes.append(m)
        print("minutes", minutes, minutes_intervals)
        # Filtra la lista de archivos
        nfiles = []
        for f in files:
            m = depot_get_minutes_from_filename(f)
            if m in minutes:
                nfiles.append(f)
            else:
                for mint in minutes_intervals:
                    if mint[0] <= m and m <= mint[1]:
                        nfiles.append(f)
        files = nfiles
                
    return files
        
if __name__== "__main__":  
    nivel = "l2"
    dominio = "conus"

    fecha1 = 2019160
    fecha2 = 2019365
    fechas = juliandates_range(fecha1, fecha2, 1)

    #fechas = juliandates_range(fecha2juliandate(fecha1), fecha2juliandate(fecha2), 1)

    destdir = "/data/tmp/AOD_average/"
    products = [ 'AOD' ]
    for fecha in fechas:
        #fecha = key
        #horas = fechoras[key]
        print(fecha)
        files = recupera_datos(nivel, dominio, [fecha])
        print(files)
        for datafile in files:
            depot_goes_extract_products(datafile, products, destdir)

    # Convertir opcionalmente a geotiff
    os.system("for i in `ls *.nc`; do nc2tiff.sh $i AOD; done")
                 
                 
