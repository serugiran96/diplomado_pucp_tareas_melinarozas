"""Paso 2: limpia las celdas de NASA POWER y las agrega por departamento, año y mes.

Entradas : datos/originales/nasa_power.csv.gz, puntos_malla.csv
Salidas  : datos/procesados/mensual_departamento.csv, anual_departamento.csv, anual_nacional.csv,
           celdas.csv y control_calidad.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent.parent
ORIGINALES = AQUI / "datos" / "originales"
PROCESADOS = AQUI / "datos" / "procesados"

NOMBRES = {"AMAZONAS": "Amazonas", "ANCASH": "Áncash", "APURIMAC": "Apurímac", "AREQUIPA": "Arequipa",
           "AYACUCHO": "Ayacucho", "CAJAMARCA": "Cajamarca", "CALLAO": "Callao", "CUSCO": "Cusco",
           "HUANCAVELICA": "Huancavelica", "HUANUCO": "Huánuco", "ICA": "Ica", "JUNIN": "Junín",
           "LA LIBERTAD": "La Libertad", "LAMBAYEQUE": "Lambayeque", "LIMA": "Lima", "LORETO": "Loreto",
           "MADRE DE DIOS": "Madre de Dios", "MOQUEGUA": "Moquegua", "PASCO": "Pasco", "PIURA": "Piura",
           "PUNO": "Puno", "SAN MARTIN": "San Martín", "TACNA": "Tacna", "TUMBES": "Tumbes", "UCAYALI": "Ucayali"}
# Agrupación propia por región natural predominante; varios departamentos abarcan más de una.
ZONAS = {"Costa": ["Tumbes", "Piura", "Lambayeque", "La Libertad", "Lima", "Callao", "Ica", "Moquegua", "Tacna"],
         "Sierra": ["Cajamarca", "Áncash", "Huánuco", "Pasco", "Junín", "Huancavelica", "Ayacucho", "Apurímac",
                    "Cusco", "Puno", "Arequipa"],
         "Selva": ["Amazonas", "San Martín", "Loreto", "Ucayali", "Madre de Dios"]}
ZONA_DE = {d: z for z, ds in ZONAS.items() for d in ds}
VARIABLES = {"T2M": "temp_media", "T2M_MAX": "temp_max", "T2M_MIN": "temp_min", "PRECTOTCORR": "lluvia_mm_dia"}
NUEVO_FALTANTE = -999


def promedio_ponderado(g, columnas):
    """Promedio por área: en una malla regular el área de cada celda es proporcional a cos(latitud)."""
    pesos = g["peso"].to_numpy()
    return pd.Series({c: np.average(g[c], weights=pesos) for c in columnas})


def main():
    PROCESADOS.mkdir(exist_ok=True)
    crudo = pd.read_csv(ORIGINALES / "nasa_power.csv.gz")
    puntos = pd.read_csv(ORIGINALES / "puntos_malla.csv")
    control = {"filas_crudas": int(len(crudo)), "celdas": int(crudo[["lat", "lon"]].drop_duplicates().shape[0])}

    # La API incluye un mes 13 con el resumen anual: se descarta y el año se recalcula desde los meses.
    control["filas_mes_13_descartadas"] = int((crudo["mes"] == 13).sum())
    df = crudo[crudo["mes"].between(1, 12)].rename(columns=VARIABLES)
    columnas = list(VARIABLES.values())

    control["duplicados_eliminados"] = int(df.duplicated(["lat", "lon", "anio", "mes"]).sum())
    df = df.drop_duplicates(["lat", "lon", "anio", "mes"])
    # -999 es el código de dato faltante de POWER; también se descartan valores físicamente imposibles.
    control["faltantes_por_variable"] = {c: int((df[c] == NUEVO_FALTANTE).sum()) for c in columnas}
    df[columnas] = df[columnas].replace(NUEVO_FALTANTE, np.nan)
    malos = (df["temp_media"].abs() > 60) | (df["lluvia_mm_dia"] < 0)
    control["valores_imposibles"] = int(malos.sum())
    df = df[~malos].dropna(subset=columnas)
    control["filas_validas"] = int(len(df))

    celdas = df[["lat", "lon", "altitud_celda"]].drop_duplicates(["lat", "lon"])
    df["dias"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1)).dt.days_in_month
    df["lluvia_mm"] = df["lluvia_mm_dia"] * df["dias"]
    df["peso"] = np.cos(np.radians(df["lat"]))
    df = df.merge(puntos[["departamento", "lat", "lon"]], on=["lat", "lon"])
    df["departamento"] = df["departamento"].map(NOMBRES)

    medidas = ["temp_media", "temp_max", "temp_min", "lluvia_mm"]
    mensual = (df.groupby(["departamento", "anio", "mes"]).apply(promedio_ponderado, medidas, include_groups=False)
               .reset_index().round(3))
    mensual.to_csv(PROCESADOS / "mensual_departamento.csv", index=False)

    agregacion = {"temp_media": "mean", "temp_max": "mean", "temp_min": "mean", "lluvia_mm": "sum"}
    n_meses = mensual.groupby(["departamento", "anio"])["mes"].transform("count")
    control["anios_incompletos"] = int((n_meses < 12).sum() / 12)
    anual = mensual[n_meses == 12].groupby(["departamento", "anio"], as_index=False).agg(agregacion).round(3)
    anual["zona"] = anual["departamento"].map(ZONA_DE)
    anual.to_csv(PROCESADOS / "anual_departamento.csv", index=False)

    # Nacional: cada celda cuenta una sola vez, ponderada por área (no un promedio de departamentos).
    nac = df.drop_duplicates(["lat", "lon", "anio", "mes"])
    nacional_m = (nac.groupby(["anio", "mes"]).apply(promedio_ponderado, medidas, include_groups=False).reset_index())
    nacional = nacional_m.groupby("anio", as_index=False).agg(agregacion).round(3)
    nacional.to_csv(PROCESADOS / "anual_nacional.csv", index=False)
    nacional_m.round(3).to_csv(PROCESADOS / "mensual_nacional.csv", index=False)

    celdas = celdas.merge(puntos[["departamento", "lat", "lon"]], on=["lat", "lon"])
    celdas["departamento"] = celdas["departamento"].map(NOMBRES)
    celdas.to_csv(PROCESADOS / "celdas.csv", index=False)

    control.update(departamentos=int(anual["departamento"].nunique()), anio_min=int(anual["anio"].min()),
                   anio_max=int(anual["anio"].max()), observaciones_mensuales=int(len(mensual)))
    (PROCESADOS / "control_calidad.json").write_text(json.dumps(control, indent=2, ensure_ascii=False))
    print(json.dumps(control, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
