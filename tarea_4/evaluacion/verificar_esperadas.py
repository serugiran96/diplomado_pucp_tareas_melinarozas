"""Verifica las respuestas esperadas de evaluacion/preguntas.csv con cálculos independientes del agente.

    uv run evaluacion/verificar_esperadas.py

- BCRP: pide cada serie directamente a la API oficial con httpx (no usa mcp/server.py).
- ENAHO: recalcula desde el zip del INEI con la sumaria y factor07 × mieperho (el método de las cifras
  oficiales), con código propio que no usa las skills.

Escribe evaluacion/verificacion_esperadas.csv. Las respuestas esperadas se fijaron antes de correr el
experimento y este script solo confirma que coinciden con las fuentes; no las modifica.
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
            return [(p["name"], float(p["values"][0])) for p in r.json()["periods"]
                    if p["values"][0] not in ("n.d.", "")]
        time.sleep(2 * (intento + 1))
    raise RuntimeError(f"El BCRP no respondió para {codigo}")


def sumaria():
    with zipfile.ZipFile(RAIZ / "datos" / "966-Modulo34.zip") as z:
        h = pd.read_stata(io.BytesIO(z.read("966-Modulo34/sumaria-2024.dta")), convert_categoricals=False)
    h.columns = h.columns.str.lower()
    h["w"] = h.factor07.astype(float) * h.mieperho
    h["pobre"] = h.pobreza <= 2
    h["dep"] = h.ubigeo.astype(str).str.zfill(6).str[:2]
    return h


def pct(d):
    return round(100 * (d.w * d.pobre).sum() / d.w.sum(), 2)


def main():
    filas = []
    inf = dict(bcrp("PM05197PA", 2022, 2024))
    filas.append(("B1_inflacion_2022", round(inf["2022"], 4), "API BCRP PM05197PA/2022"))
    filas.append(("B2_pbi_2024", round(dict(bcrp("PM04923AA", 2024, 2024))["2024"], 4), "API BCRP PM04923AA/2024"))
    filas.append(("B3_tc_dic2024", round(bcrp("PN01206PM", "2024-12", "2024-12")[0][1], 4),
                  "API BCRP PN01206PM/2024-12"))
    serie = bcrp("PN01273PM", "2020-1", "2024-12")
    mes, val = max(serie, key=lambda x: x[1])
    filas.append(("B4_max_inflacion", f"{mes}; {val:.4f}", "API BCRP PN01273PM/2020-1/2024-12, máximo"))

    h = sumaria()
    deps = h.groupby("dep").apply(pct, include_groups=False)
    nombres = pd.read_csv(RAIZ / ".claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv",
                          dtype={"ccdd": str}).set_index("ccdd").departamento
    urb, rur = pct(h[h.estrato <= 5]), pct(h[h.estrato >= 6])
    filas.append(("E1_pobreza_nacional", pct(h), "sumaria 2024, factor07 × mieperho"))
    filas.append(("E2_pobreza_rural", rur, "sumaria 2024, estrato >= 6"))
    filas.append(("E3_pobreza_cusco", deps["08"], "sumaria 2024, ubigeo[:2] == 08"))
    filas.append(("E4_max_departamento", f"{nombres[deps.idxmax()].title()}; {deps.max():.2f}",
                  "sumaria 2024, máximo por ubigeo[:2]"))
    filas.append(("M1_inflacion_y_pobreza", f"{inf['2024']:.4f}; {pct(h)}; no (criterio)",
                  "API BCRP PM05197PA/2024 + sumaria 2024"))
    filas.append(("M2_caida_inflacion_y_brecha", f"{inf['2022'] - inf['2024']:.4f}; {rur - urb:.2f}",
                  "API BCRP PM05197PA 2022-2024 + sumaria 2024 (rural - urbana)"))

    preg = pd.read_csv(RAIZ / "evaluacion" / "preguntas.csv").set_index("id")
    out = pd.DataFrame(filas, columns=["id", "recalculado", "procedimiento"])
    out.insert(1, "esperado", out.id.map(preg.valores_esperados))
    out.insert(2, "tolerancias", out.id.map(preg.tolerancias))

    def coincide(fila):
        esperados = str(fila.esperado).split(";")
        recalc = [x.strip() for x in str(fila.recalculado).replace(" (criterio)", "").split(";")]
        tols = str(fila.tolerancias).split(";")
        for e, r, t in zip(esperados, recalc, tols):
            if t == "exacto":
                norm = {"Jun.2022": "2022-06"}.get(r, r)
                if norm.lower() != e.lower():
                    return False
            elif abs(float(e) - float(r)) > float(t):
                return False
        return True

    out["coincide"] = out.apply(coincide, axis=1)
    out.to_csv(RAIZ / "evaluacion" / "verificacion_esperadas.csv", index=False)
    print(out.to_string(index=False))
    print(f"\n{out.coincide.sum()}/{len(out)} respuestas esperadas confirmadas con cálculos independientes.")


if __name__ == "__main__":
    main()
