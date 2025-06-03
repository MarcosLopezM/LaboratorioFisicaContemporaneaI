import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.size": 12,
        "font.serif": ["Computer Modern"],
    }
)

# Fondo de plasma apagado
src_path_VIS = "./Analisis/01abr2025-wo_duplicate/VIS/"
src_path_UV = "./Analisis/01abr2025-wo_duplicate/UV/"


# Función para calcular el promedio del ruido de fondo
def calcular_promedio_cuentas(directorio, file_start=0, file_end=None):
    # Número de archivos a procesar
    archivos = sorted(os.listdir(directorio))[file_start:file_end]

    # Nos aseguramos de que haya archivos en el rango especificado
    if not archivos:
        raise ValueError("No se encontraron archivos en el rango especificado.")

    # Cambiamos la forma del dataframe para calcular el promedio correspondiente a cada lonigtud de onda
    df_cuentas = pd.concat(
        [
            pd.read_csv(
                os.path.join(directorio, archivo), sep=";", skiprows=5, usecols=[1]
            ).drop(index=0)
            for archivo in archivos
        ],
        axis=1,
    )

    # Convertimos el tipo de dato a numérico y calculamos el promedio de las cuentas
    df_cuentas = df_cuentas.apply(pd.to_numeric, errors="coerce")
    promedio = df_cuentas.mean(axis=1).reset_index(drop=True)

    # Agregamos las longitudes de onda
    longitudes = pd.read_csv(
        os.path.join(directorio, archivos[0]), sep=";", skiprows=5, usecols=[0]
    ).drop(index=0)
    longitudes = longitudes.apply(pd.to_numeric, errors="coerce").reset_index(drop=True)

    df = pd.concat([longitudes, promedio], axis=1)
    df.columns = ["Wave", "Mean"]

    return df


#### Promedio de ruido de fondo ####
### Promedio de ruido de fondo UV ###
df_uv = calcular_promedio_cuentas(src_path_UV, file_end=15)

### Promedio de ruido de fondo VIS ###
df_vis = calcular_promedio_cuentas(src_path_VIS, file_end=15)


# Función para quitar el ruido de fondo de los espectrso
def limpiar_ruido(df, ruido):
    if not df["Wave"].equals(ruido["Wave"]):
        raise ValueError("Las longitudes de onda no coinciden.")

    df_limpio = df.copy()
    df_limpio["Mean"] = df["Mean"] - ruido["Mean"]
    df_limpio["Mean"] = df_limpio["Mean"].clip(
        lower=0
    )  # Quitamos los valores negativos

    return df_limpio


### Promedio antes de abrir el shutter ###
df_uv_before = calcular_promedio_cuentas(src_path_UV, 16, 87)
df_vis_before = calcular_promedio_cuentas(src_path_VIS, 16, 87)

### Promedio después de abrir el shutter ###
df_uv_after = calcular_promedio_cuentas(src_path_UV, 87, 576)
df_vis_after = calcular_promedio_cuentas(src_path_VIS, 87, 576)

#### Espectros sin el ruido de fondo ####
### Espectro antes de abrir el shutter ###
df_bf_clean_uv = limpiar_ruido(df_uv_before, df_uv)
df_bf_clean_vis = limpiar_ruido(df_vis_before, df_vis)
df_before = pd.concat([df_bf_clean_uv, df_bf_clean_vis])
df_before = df_before.sort_values("Wave").reset_index(drop=True)

### Espectro después de abrir el shutter ###
df_af_clean_uv = limpiar_ruido(df_uv_after, df_uv)
df_af_clean_vis = limpiar_ruido(df_vis_after, df_vis)
df_after = pd.concat([df_af_clean_uv, df_af_clean_vis])
df_after = df_after.sort_values("Wave").reset_index(drop=True)

######## Gráficas de los espectros con las líneas de emisión para cada elemento ########
lineas = pd.read_csv("./Analisis/lineas_new.csv")
lineas = lineas[
    lineas["intens"] > 5000
]  # Elegimos las líneas de emisión con mayor intensidad
wavelength = lineas["ritz_wl_air(nm)"]
intensidad = lineas["intens"]

# Creamos una columna para el elemento y su estado
lineas["ele_sp"] = lineas["element"] + " " + np.where(lineas["sp_num"] == 1, "I", "II")
# Condiciones para los distintios elementos
conditions = [
    lineas["ele_sp"] == "B I",
    lineas["ele_sp"] == "B II",
    lineas["ele_sp"] == "N I",
    lineas["ele_sp"] == "Ar I",
]
# Colores y etiquetas
colors = ["#00FF00", "#FFA500", "#00CED1", "#FF69B4"]


### Graficamos las líneas de emisión ###
def emission_lines(ax, lineas, conditions, colors):
    labels = set()
    for i, condition in enumerate(conditions):
        filtered_lines = lineas[condition]

        if not filtered_lines.empty:
            sp_num = filtered_lines["sp_num"].iloc[0]
            ele_label = filtered_lines["ele_sp"].iloc[0]
            ls = "--" if sp_num == 2 else "-"
            color = colors[i % len(colors)]

            # Líneas verticales
            for wl, intens in zip(
                filtered_lines["ritz_wl_air(nm)"],
                filtered_lines["intens"],
            ):
                label = ele_label if ele_label not in labels else None
                if label:
                    labels.add(label)

                # Normalizamos la intensidad
                intens_norm = intens / filtered_lines["intens"].max()

                if sp_num == 2:  # Ionizado
                    ax.axvline(
                        wl,
                        0,
                        intens_norm,
                        # alpha=0.3,
                        color=color,
                        linestyle=ls,
                        label=label,
                    )
                else:  # Excitado
                    ax.axvline(
                        wl,
                        0,
                        intens,
                        # alpha=0.3,
                        color=color,
                        linestyle=ls,
                        label=label,
                    )


fig, ax = plt.subplots(figsize=(13, 7))
emission_lines(ax, lineas, conditions, colors)
ax.set_xlabel("Longitud de onda (nm)")
ax.set_ylabel("Intensidad (a.u.)")
ax.set_title(
    "Líneas de emisión más intensas obtenidas del NIST Atomic Spectra Database"
)
ax.legend(
    loc=2,
)
fig.savefig("./figs/lineas_emision.jpg", dpi=300)
plt.show()
plt.close(fig)

### Graficamos los espectros ###
## Espectro antes de abrir el shutter
wl_bf = df_before["Wave"]
intens_bf = df_before["Mean"]
## Espectro después de abrir el shutter
wl_af = df_after["Wave"]
intens_af = df_after["Mean"]

fig, ax = plt.subplots(figsize=(13, 7))
emission_lines(ax, lineas, conditions, colors)
ax.plot(
    wl_bf,
    intens_bf,
    label="Antes de abrir el shutter",
    color="#1B9E77",
    alpha=0.8,
)
ax.plot(
    wl_af,
    intens_af,
    label="Después de abrir el shutter",
    color="#984EA3",
    alpha=0.8,
)
ax.set_xlabel("Longitud de onda (nm)")
ax.set_ylabel("Intensidad (a.u.)")
ax.set_title(
    "Espectrometría de emisión óptica de plasma de BN generado por Rf Magnetron Sputtering"
)
ax.legend(loc=2, fontsize=6)
ax.margins(y=0)
fig.savefig("./figs/espectroBN.jpg", dpi=300)
plt.show()
