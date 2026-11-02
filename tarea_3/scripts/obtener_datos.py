"""Paso 1: descarga la temperatura y la lluvia mensual de cada departamento del Perú.

Fuente principal: NASA POWER (API mensual por punto, 1981-2025). Cada departamento se representa con
los puntos de una malla de 0.5° que caen dentro de su polígono. Las respuestas crudas se guardan en
datos/originales/nasa_power.csv.gz junto con la fecha de descarga.

Contraste independiente: ERA5 puro (vía Open-Meteo, models=era5) en un punto interior de cada departamento,
para comprobar que las tendencias no dependen de un solo producto. La opción por defecto de Open-Meteo puede
combinar varios modelos y dio resultados distintos, por eso se fija el modelo. Salidas: era5_centroides.csv y
era5_lluvia_centroides.csv en datos/originales/.

Uso: python scripts/obtener_datos.py [--solo-nasa | --solo-era5]
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from shapely.geometry import Point, shape

AQUI = Path(__file__).resolve().parent.parent
ORIGINALES = AQUI / "datos" / "originales"
GEOJSON = ORIGINALES / "peru_departamental.geojson"
NASA = ORIGINALES / "nasa_power.csv.gz"
ERA5 = ORIGINALES / "era5_centroides.csv"
ERA5_LLUVIA = ORIGINALES / "era5_lluvia_centroides.csv"
PUNTOS = ORIGINALES / "puntos_malla.csv"
REGISTRO = ORIGINALES / "registro_descarga.json"

INICIO, FIN = 1981, 2025
PASO = 0.5                # grados; coincide con la resolución latitudinal de MERRA-2
MIN_PUNTOS = 3            # los departamentos pequeños reciben puntos extra alrededor del centroide
PARAMETROS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR"
URL_NASA = "https://power.larc.nasa.gov/api/temporal/monthly/point"
URL_ERA5 = "https://archive-api.open-meteo.com/v1/archive"


def departamentos():
    with open(GEOJSON, encoding="utf-8") as f:
        return [(x["properties"]["NOMBDEP"], x["properties"]["FIRST_IDDP"], shape(x["geometry"]))
                for x in json.load(f)["features"]]


def malla():
    """Puntos de la malla de 0.5° dentro de cada departamento."""
    filas = []
    for nombre, ubigeo, poligono in departamentos():
        minx, miny, maxx, maxy = poligono.bounds
        lon0 = PASO * (minx // PASO)
        lat0 = PASO * (miny // PASO)
        puntos = []
        lat = lat0
        while lat <= maxy:
            lon = lon0
            while lon <= maxx:
                if poligono.contains(Point(lon, lat)):
                    puntos.append((round(lat, 3), round(lon, 3)))
                lon += PASO
            lat += PASO
        if len(puntos) < MIN_PUNTOS:      # Callao, Tumbes, etc.: centroide y puntos internos adicionales
            c = poligono.representative_point()
            puntos.append((round(c.y, 3), round(c.x, 3)))
            for dx, dy in [(0.15, 0), (-0.15, 0), (0, 0.15), (0, -0.15), (0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)]:
                if len(puntos) >= MIN_PUNTOS:
                    break
                if poligono.contains(Point(c.x + dx, c.y + dy)):
                    puntos.append((round(c.y + dy, 3), round(c.x + dx, 3)))
        for lat, lon in puntos:
            filas.append({"departamento": nombre, "ubigeo": ubigeo, "lat": lat, "lon": lon})
    return pd.DataFrame(filas)


def bajar_punto(lat, lon, intentos=5):
    params = {"parameters": PARAMETROS, "community": "AG", "longitude": lon, "latitude": lat,
              "start": INICIO, "end": FIN, "format": "JSON"}
    for i in range(intentos):
        try:
            r = requests.get(URL_NASA, params=params, timeout=90)
            r.raise_for_status()
            j = r.json()
            filas = {}
            for var, serie in j["properties"]["parameter"].items():
                for clave, valor in serie.items():
                    filas.setdefault(clave, {})[var] = valor
            altitud = j["geometry"]["coordinates"][2]
            return [{"lat": lat, "lon": lon, "altitud_celda": altitud, "anio": int(k[:4]), "mes": int(k[4:]), **v}
                    for k, v in filas.items()]
        except Exception as e:  # noqa: BLE001  la API falla de forma intermitente
            print(f"  reintento {i + 1} ({lat}, {lon}): {e}", file=sys.stderr, flush=True)
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"No se pudo descargar ({lat}, {lon})")


def nasa():
    puntos = malla()
    puntos.to_csv(PUNTOS, index=False)
    unicos = puntos[["lat", "lon"]].drop_duplicates()
    print(f"{len(puntos)} puntos, {len(unicos)} únicos", flush=True)
    filas, t = [], time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        tareas = [ex.submit(bajar_punto, r.lat, r.lon) for r in unicos.itertuples()]
        for i, tarea in enumerate(as_completed(tareas), 1):
            filas.extend(tarea.result())
            if i % 25 == 0:
                print(f"{i}/{len(unicos)} [{time.time() - t:.0f}s]", flush=True)
    df = pd.DataFrame(filas).sort_values(["lat", "lon", "anio", "mes"])
    df.to_csv(NASA, index=False)
    print(f"Guardado {NASA.name}: {len(df):,} filas", flush=True)
    registrar("nasa_power", URL_NASA, len(df))


def pedir_era5(params, nombre, intentos=80):
    for _ in range(intentos):
        try:
            r = requests.get(URL_ERA5, params=params, timeout=(30, 180))
        except requests.RequestException as e:
            print(f"  sin respuesta, espero 70 s ({nombre}): {type(e).__name__}", flush=True)
            time.sleep(70)
            continue
        if r.status_code == 429:
            print(f"  límite de la API, espero 70 s ({nombre})", flush=True)
            time.sleep(70)
            continue
        try:
            r.raise_for_status()
            r.json()["daily"]
            return r
        except (requests.RequestException, ValueError, KeyError) as e:   # respuesta incompleta de la API
            print(f"  respuesta inválida, espero 70 s ({nombre}): {type(e).__name__}", flush=True)
            time.sleep(70)
    raise RuntimeError(f"ERA5 no respondió para {nombre}")


def era5():
    filas = []
    previos = pd.read_csv(ERA5) if ERA5.exists() else pd.DataFrame(columns=["departamento"])
    hechos = set(previos["departamento"])
    for nombre, _, poligono in departamentos():
        if nombre in hechos:
            continue
        c = poligono.representative_point()
        params = {"latitude": round(c.y, 3), "longitude": round(c.x, 3), "start_date": f"{INICIO}-01-01",
                  "end_date": f"{FIN}-12-31", "daily": "temperature_2m_mean", "timezone": "America/Lima", "models": "era5"}
        r = pedir_era5(params, nombre)
        d = pd.DataFrame(r.json()["daily"])
        d["anio"] = pd.to_datetime(d["time"]).dt.year
        anual = d.groupby("anio", as_index=False)["temperature_2m_mean"].mean().round(3)
        anual.insert(0, "departamento", nombre)
        filas.append(anual)
        pd.concat([previos, *filas]).to_csv(ERA5, index=False)
        print(f"ERA5 {nombre}", flush=True)
        time.sleep(15)
    registrar("era5_open_meteo", URL_ERA5, len(pd.read_csv(ERA5)))


def era5_lluvia():
    """Lluvia ERA5 en un punto de cada departamento; retoma lo ya descargado porque la API limita las series largas por hora."""
    filas = []
    previos = pd.read_csv(ERA5_LLUVIA) if ERA5_LLUVIA.exists() else pd.DataFrame(columns=["departamento"])
    hechos = set(previos["departamento"])
    for nombre, _, poligono in departamentos():
        if nombre in hechos:
            continue
        c = poligono.representative_point()
        params = {"latitude": round(c.y, 3), "longitude": round(c.x, 3), "start_date": f"{INICIO}-01-01",
                  "end_date": f"{FIN}-12-31", "daily": "precipitation_sum", "timezone": "America/Lima", "models": "era5"}
        r = pedir_era5(params, nombre)
        d = pd.DataFrame(r.json()["daily"])
        d["anio"] = pd.to_datetime(d["time"]).dt.year
        anual = d.groupby("anio", as_index=False)["precipitation_sum"].sum().round(2)
        anual.insert(0, "departamento", nombre)
        filas.append(anual)
        pd.concat([previos, *filas]).to_csv(ERA5_LLUVIA, index=False)
        print(f"ERA5 lluvia {nombre}", flush=True)
        time.sleep(15)
    registrar("era5_lluvia_open_meteo", URL_ERA5, len(pd.read_csv(ERA5_LLUVIA)))


def registrar(nombre, url, filas):
    registro = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else {}
    registro[nombre] = {"url": url, "filas": filas, "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    REGISTRO.write_text(json.dumps(registro, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-nasa", action="store_true")
    ap.add_argument("--solo-era5", action="store_true")
    a = ap.parse_args()
    if not a.solo_era5:
        nasa()
    if not a.solo_nasa:
        era5()
        era5_lluvia()
