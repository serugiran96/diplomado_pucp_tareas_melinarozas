"""Descarga las fotografías del reel desde Wikimedia Commons y registra autor y licencia en reel/recursos/fotos/creditos.json."""
import json
import re
import time
from pathlib import Path

import requests

DESTINO = Path(__file__).resolve().parent.parent / "reel" / "recursos" / "fotos"
FOTOS = {"ucayali": "File:The Ucayali River in the lowland Amazon rainforest of central Peru (iss074e0492148).jpg",
         "ica": "File:Desert - Ica - panoramio.jpg",
         "andes": "File:ISS-59 Andes mountain range, Peru.jpg"}
UA = {"User-Agent": "TareaPUCP/1.0 (curso de Python, uso educativo)"}


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    creditos = {}
    for clave, titulo in FOTOS.items():
        j = requests.get("https://commons.wikimedia.org/w/api.php", timeout=40, headers=UA, params={
            "action": "query", "titles": titulo, "prop": "imageinfo", "iiprop": "url|extmetadata",
            "iiurlwidth": 2000, "format": "json"}).json()
        info = next(iter(j["query"]["pages"].values()))["imageinfo"][0]
        meta = info["extmetadata"]
        for url in (info["thumburl"], info["url"]):   # si la miniatura no se puede generar, se usa el original
            r = requests.get(url, timeout=120, headers=UA)
            if r.ok and r.headers.get("content-type", "").startswith("image/"):
                (DESTINO / f"{clave}.jpg").write_bytes(r.content)
                break
            time.sleep(5)
        else:
            raise RuntimeError(f"No se pudo bajar {titulo}")
        time.sleep(3)
        creditos[clave] = {"titulo": titulo, "autor": re.sub("<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip(),
                           "licencia": meta.get("LicenseShortName", {}).get("value", ""),
                           "url": info["descriptionurl"]}
    (DESTINO / "creditos.json").write_text(json.dumps(creditos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(creditos, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
