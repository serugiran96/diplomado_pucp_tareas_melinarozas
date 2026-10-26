"""Descarga el corpus de la Tarea 2 a partir de datos/fuentes.csv.

Uso:
    python datos.py            # descarga todo lo que falte
    python datos.py audio      # solo la modalidad audio
    python datos.py documento  # solo la modalidad documento

Cada fila de fuentes.csv trae la URL de descarga directa (url_descarga) y la
ruta local (archivo_original). Los archivos crudos quedan en datos/raw/, que
no se sube a GitHub (.gitignore): este script es la receta para recuperarlos.
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

CARPETA = Path(__file__).parent
# Wikimedia y archive.org piden un User-Agent que identifique al proyecto.
USER_AGENT = "TareaPUCP-corpus/0.1 (https://github.com/melinaroz; proyecto academico diplomado PUCP)"
PAUSA_SEGUNDOS = 1.5


def descargar_url(url, destino, intentos=8):
    # Con conexiones inestables la descarga se corta a medias: guardamos en un
    # .part y, si falla, retomamos desde el último byte con un encabezado Range.
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(destino.suffix + ".part")
    for intento in range(intentos):
        ya_bajado = temporal.stat().st_size if temporal.exists() else 0
        encabezados = {"User-Agent": USER_AGENT}
        if ya_bajado > 0:
            encabezados["Range"] = f"bytes={ya_bajado}-"
        try:
            respuesta = requests.get(url, headers=encabezados, stream=True, timeout=(15, 30))
            if respuesta.status_code == 416:
                break
            respuesta.raise_for_status()
            # Si el servidor ignora el Range (responde 200), empezamos de cero.
            modo = "ab" if respuesta.status_code == 206 else "wb"
            with open(temporal, modo) as archivo:
                for bloque in respuesta.iter_content(chunk_size=1 << 16):
                    archivo.write(bloque)
            break
        except requests.RequestException as error:
            print(f"   intento {intento + 1} falló ({error}); reintentando")
            time.sleep(5)
    else:
        raise RuntimeError(f"No se pudo descargar {url}")
    temporal.rename(destino)


def descargar_de_zip(url_zip, miembro, destino):
    # OpenSLR 73 publica zips de ~900 MB. remotezip lee solo los bytes del
    # archivo que pedimos (peticiones HTTP Range), sin bajar el zip entero.
    from remotezip import RemoteZip

    destino.parent.mkdir(parents=True, exist_ok=True)
    with RemoteZip(url_zip, headers={"User-Agent": USER_AGENT}) as zip_remoto:
        destino.write_bytes(zip_remoto.read(miembro))


def main():
    fuentes = pd.read_csv(CARPETA / "datos" / "fuentes.csv", dtype=str)
    if len(sys.argv) > 1:
        fuentes = fuentes[fuentes["modalidad"] == sys.argv[1]]

    for fila in fuentes.itertuples():
        destino = CARPETA / fila.archivo_original
        if destino.exists():
            print(f"{fila.id}: ya existe")
            continue
        print(f"{fila.id}: descargando {fila.url_descarga[:90]}")
        # Las filas de OpenSLR usan la forma  <url del zip>::<archivo dentro del zip>
        if "::" in fila.url_descarga:
            url_zip, miembro = fila.url_descarga.split("::")
            descargar_de_zip(url_zip, miembro, destino)
        else:
            descargar_url(fila.url_descarga, destino)
        time.sleep(PAUSA_SEGUNDOS)


if __name__ == "__main__":
    main()
