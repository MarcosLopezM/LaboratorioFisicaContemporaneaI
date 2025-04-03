import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern"],
    "font.size": 12,
})

## Promedio de ruido de fondo
def calcular_promedio_cuentas(directorio, file_start=0, file_end=None):
    # Número de archivos a procesar
    archivos = sorted(os.listdir(directorio))[file_start:file_end]

    # Unir el resto de los archivos
    df_cuentas = pd.concat([pd.read_csv(os.path.join(directorio, archivo), sep=";", skiprows=5, usecols=[1]).drop(index=0) for archivo in archivos], axis=1)
    
    # Convertimos los datos a numéricos
    df_cuentas = df_cuentas.apply(pd.to_numeric, errors='coerce')

    # Calculamos el promedio de las cuentas
    promedio = df_cuentas.mean(axis=1)

    # Agregamos la longitud de onda
    df = pd.concat([pd.read_csv(os.path.join(directorio, archivos[0]), sep=";", skiprows=5, usecols=[0]).drop(index=0), promedio], axis=1)
    df = df.apply(pd.to_numeric, errors='coerce')
    
    # Renombramos las columnas
    df.columns = ['Wave', 'Mean']

    return df

####### Promedios UV #######
src_path_UV = os.path.abspath("../01abr2025-wo_duplicate/UV/")

## Promedio de ruido de fondo ##
df_bg_uv = calcular_promedio_cuentas(src_path_UV, file_start=0, file_end=15)

## Promedio antes de abrir el shutter ##
df_bf_shutter_uv = calcular_promedio_cuentas(src_path_UV, file_start=16, file_end=87)

## Promedio después de abrir el shutter ##
df_aft_shutter_uv = calcular_promedio_cuentas(src_path_UV, file_start=87, file_end=576)

####### Promedios VIS #######
src_path_VIS = os.path.abspath("../01abr2025-wo_duplicate/VIS/")

## Promedio de ruido de fondo ##
df_bg_vis = calcular_promedio_cuentas(src_path_VIS, file_start=0, file_end=15)

## Promedio antes de abrir el shutter ##
df_bf_shutter_vis = calcular_promedio_cuentas(src_path_VIS, file_start=16, file_end=87)

## Promedio después de abrir el shutter ##
df_aft_shutter_vis = calcular_promedio_cuentas(src_path_VIS, file_start=87, file_end=576)


####### Quitando el ruido de fondo #######
## Ruido UV ##
df_bf_shutter_uv['Counts'] = df_bf_shutter_uv['Mean'] - df_bg_uv['Mean']
df_aft_shutter_uv['Counts'] = df_aft_shutter_uv['Mean'] - df_bg_uv['Mean']

## Ruido VIS ##
df_bf_shutter_vis['Counts'] = df_bf_shutter_vis['Mean'] - df_bg_vis['Mean']
df_aft_shutter_vis['Counts'] = df_aft_shutter_vis['Mean'] - df_bg_vis['Mean']


####### Espectro de emisión #######
plt.figure(figsize=(13, 7))

# Cargar el archivo CSV con los datos de las líneas espectrales
df_lines = pd.read_csv("../lineas_new.csv")

wavelength = df_lines['ritz_wl_air(nm)']
intensidad = df_lines['intens']

# Crear una columna para el elemento y el número
df_lines['element_sp'] = df_lines['element'] + ' ' + np.where(df_lines['sp_num'] == 1, 'I', 'II')


conditions = [
    df_lines['element_sp'] == 'B I',
    df_lines['element_sp'] == 'B II',
    df_lines['element_sp'] == 'N I',
    df_lines['element_sp'] == 'Ar I',
]

for condition in conditions:
    scatter = plt.scatter(df_lines[condition]['ritz_wl_air(nm)'], df_lines[condition]['intens'], label=df_lines[condition]['element_sp'].iloc[0], alpha=0.1) 

    color = scatter.get_facecolors()[0]
    sp_num = df_lines[condition]['sp_num'].iloc[0]
    linestyle = '--' if sp_num == 2 else '-'

    # Líneas verticales
    for wl, intens in zip(df_lines[condition]['ritz_wl_air(nm)'], df_lines[condition]['intens']):
        if sp_num == 2: # Ionizado
            plt.axvline(wl, 0, intens, alpha=0.3, color=color, linestyle=linestyle)
        else: # Excitado
            plt.axvline(wl, 0, intens, alpha=0.3, color=color, linestyle=linestyle)


plt.scatter(df_bf_shutter_uv['Wave'], df_bf_shutter_uv['Counts'], label='Antes del obturador')
plt.scatter(df_aft_shutter_uv['Wave'], df_aft_shutter_uv['Counts'], label='Después del obturador')
plt.scatter(df_bf_shutter_vis['Wave'], df_bf_shutter_vis['Counts'], label='Antes del obturador')
plt.scatter(df_aft_shutter_vis['Wave'], df_aft_shutter_vis['Counts'], label='Después del obturador')

plt.xlabel("Longitud de onda (nm)")
plt.ylabel("Intensidad (a.u.)")
plt.title("Espectrometría de emisión óptica de plasma de BN generado por Radio Frequency Magnetron Sputtering")

plt.legend(loc="upper left", fontsize=6)
plt.show()
