"""Recalcula de forma independiente seis afirmaciones numéricas del informe final (tres del BCRP, tres de la ENAHO).

    uv run informes/verificar_cifras.py

- BCRP: pide cada serie directamente a la API oficial con httpx, sin pasar por el servidor MCP.
- ENAHO: recalcula desde el zip del INEI con la sumaria y factor07 × mieperho (el método de las cifras oficiales),
  con código propio que no usa las skills, y compara con las cifras publicadas por el INEI.
Escribe informes/verificacion_cifras.csv. El detalle y los enlaces para revisar a mano están en verificacion_cifras.md.
"""
import io
import time
import zipfile
from pathlib import Path

import httpx
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def bcrp(codigo, desde, hasta):
    for intento in range(5):
        r = httpx.get(f"{API}/{codigo}/json/{desde}/{hasta}", timeout=30)
        if r.text.lstrip().startswith("{"):
            return [(p["name"], float(p["values"][0])) for p in r.json()["periods"] if p["values"][0] != "n.d."]
        time.sleep(2 * (intento + 1))
    raise RuntimeError(codigo)


def main():
    with zipfile.ZipFile(RAIZ / "datos" / "966-Modulo34.zip") as z:
        h = pd.read_stata(io.BytesIO(z.read("966-Modulo34/sumaria-2024.dta")), convert_categoricals=False)
    h.columns = h.columns.str.lower()
    h["w"] = h.factor07.astype(float) * h.mieperho
    h["pobre"] = h.pobreza <= 2
    pct = lambda d: round(100 * float((d.w * d.pobre).sum() / d.w.sum()), 2)
    urb, rur = pct(h[h.estrato <= 5]), pct(h[h.estrato >= 6])
    caj = pct(h[h.ubigeo.astype(str).str.zfill(6).str[:2] == "06"])
    mes, maximo = max(bcrp("PN01273PM", "2020-1", "2024-12"), key=lambda x: x[1])

    filas = [
        ("1", "BCRP", "Inflación anual dic/dic de Lima en 2024: 1.97 %", 1.97,
         round(dict(bcrp("PM05197PA", 2024, 2024))["2024"], 4), "API BCRP PM05197PA/2024", 0.005),
        ("2", "BCRP", "Máximo de la inflación a 12 meses 2020-2024: 8.81 % en junio de 2022", 8.81,
         round(maximo, 4), f"API BCRP PN01273PM 2020-1/2024-12, máximo en {mes}", 0.005),
        ("3", "BCRP", "Crecimiento del PBI real en 2024: 3.52 %", 3.52,
         round(dict(bcrp("PM04923AA", 2024, 2024))["2024"], 4), "API BCRP PM04923AA/2024", 0.005),
        ("4", "ENAHO", "Pobreza monetaria nacional 2024: 27.5 % (personas, facpob07)", 27.53, pct(h),
         "sumaria 2024, factor07 × mieperho; INEI publicó 27.6 %", 0.1),
        ("5", "ENAHO", "Brecha rural - urbana 2024: 14.7 puntos (39.4 % frente a 24.7 %)", 14.70, round(rur - urb, 2),
         f"sumaria 2024: rural {rur} %, urbana {urb} %; INEI publicó 39.3 % y 24.8 % (14.5 pp)", 0.3),
        ("6", "ENAHO", "Cajamarca, el departamento más pobre en 2024: 45.0 %", 45.00, caj,
         "sumaria 2024, ubigeo[:2] == 06; INEI publicó 45.0 %", 0.1),
    ]
    out = pd.DataFrame(filas, columns=["n", "fuente", "afirmacion", "valor_informe", "valor_recalculado",
                                       "procedimiento", "tolerancia"])
    out["diferencia"] = (out.valor_informe - out.valor_recalculado).round(4)
    out["coincide"] = out.diferencia.abs() <= out.tolerancia + 1e-9
    out.to_csv(RAIZ / "informes" / "verificacion_cifras.csv", index=False)
    print(out[["n", "afirmacion", "valor_informe", "valor_recalculado", "diferencia", "coincide"]].to_string(index=False))


if __name__ == "__main__":
    main()
