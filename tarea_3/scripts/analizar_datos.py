"""Paso 3: indicadores y pruebas. Calcula tendencias, cambios entre periodos y el contraste con ERA5.

Salidas: datos/procesados/indicadores_departamento.csv, tendencias_celdas.csv, resultados.json
         web/data/clima.json (lo que usa el dashboard)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

AQUI = Path(__file__).resolve().parent.parent
ORIGINALES = AQUI / "datos" / "originales"
PROCESADOS = AQUI / "datos" / "procesados"
WEB = AQUI / "web" / "data"

P1, P2 = (1981, 2000), (2006, 2025)   # dos periodos de 20 años sin traslape
BASE = (1991, 2020)                   # normal climatológica de la OMM para las anomalías


def tendencia(anios, valores):
    """Pendiente por década (OLS) con IC 95 %, más Theil-Sen y Mann-Kendall, robustos a años extremos."""
    r = stats.linregress(anios, valores)
    t = stats.t.ppf(0.975, len(anios) - 2)
    sen = stats.theilslopes(valores, anios)[0]
    return {"por_decada": r.slope * 10, "ic95": t * r.stderr * 10, "p_ols": r.pvalue,
            "sen_por_decada": sen * 10, "p_mk": stats.kendalltau(anios, valores).pvalue}


def benjamini_hochberg(p):
    """Corrige por probar 25 departamentos a la vez."""
    p = np.asarray(p)
    orden = np.argsort(p)
    q = p[orden] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    salida = np.empty(len(p))
    salida[orden] = np.minimum(q, 1)
    return salida


def periodo(d, rango):
    return d[d["anio"].between(*rango)]


def indicadores(anual, altitud):
    filas = []
    for dep, d in anual.groupby("departamento"):
        d = d.sort_values("anio")
        t, tmax, tmin, ll = (tendencia(d["anio"], d[c]) for c in ["temp_media", "temp_max", "temp_min", "lluvia_mm"])
        a, b = periodo(d, P1), periodo(d, P2)
        filas.append({"departamento": dep, "zona": d["zona"].iloc[0],
                      "altitud_m": altitud[dep],
                      "temp_media_p2": b["temp_media"].mean(),
                      "tend_temp": t["por_decada"], "tend_temp_ic95": t["ic95"], "tend_temp_sen": t["sen_por_decada"],
                      "p_temp": t["p_mk"], "tend_max": tmax["por_decada"], "tend_min": tmin["por_decada"],
                      "cambio_temp": b["temp_media"].mean() - a["temp_media"].mean(),
                      "cambio_max": b["temp_max"].mean() - a["temp_max"].mean(),
                      "cambio_min": b["temp_min"].mean() - a["temp_min"].mean(),
                      "lluvia_p1": a["lluvia_mm"].mean(), "lluvia_p2": b["lluvia_mm"].mean(),
                      "cambio_lluvia_pct": 100 * (b["lluvia_mm"].mean() / a["lluvia_mm"].mean() - 1),
                      "cambio_lluvia_mm": b["lluvia_mm"].mean() - a["lluvia_mm"].mean(),
                      "tend_lluvia_mm": ll["por_decada"], "p_lluvia": ll["p_mk"],
                      "tend_lluvia_pct": 100 * ll["por_decada"] / d["lluvia_mm"].mean(),
                      "anio_mas_calido": int(d.loc[d["temp_media"].idxmax(), "anio"]),
                      "cv_lluvia_p1": a["lluvia_mm"].std() / a["lluvia_mm"].mean(),
                      "cv_lluvia_p2": b["lluvia_mm"].std() / b["lluvia_mm"].mean()})
    t = pd.DataFrame(filas)
    t["q_temp"] = benjamini_hochberg(t["p_temp"])
    t["q_lluvia"] = benjamini_hochberg(t["p_lluvia"])
    return t.sort_values("tend_temp", ascending=False)


def tendencias_celdas():
    crudo = pd.read_csv(ORIGINALES / "nasa_power.csv.gz")
    crudo = crudo[crudo["mes"].between(1, 12)]
    a = crudo.groupby(["lat", "lon", "altitud_celda", "anio"], as_index=False).agg(t=("T2M", "mean"), ll=("PRECTOTCORR", "mean"))
    filas = []
    for (lat, lon, alt), d in a.groupby(["lat", "lon", "altitud_celda"]):
        filas.append({"lat": lat, "lon": lon, "altitud": alt,
                      "tend_temp": stats.linregress(d["anio"], d["t"]).slope * 10,
                      "tend_lluvia_pct": 100 * stats.linregress(d["anio"], d["ll"]).slope * 10 / d["ll"].mean()})
    return pd.DataFrame(filas)


def nasa_en_punto():
    """Serie anual de NASA POWER en la celda más cercana al punto donde se consultó ERA5."""
    from shapely.geometry import shape
    from procesar_datos import NOMBRES
    crudo = pd.read_csv(ORIGINALES / "nasa_power.csv.gz")
    crudo = crudo[crudo["mes"].between(1, 12)].copy()
    crudo["dias"] = pd.to_datetime(dict(year=crudo["anio"], month=crudo["mes"], day=1)).dt.days_in_month
    crudo["lluvia_mm"] = crudo["PRECTOTCORR"] * crudo["dias"]
    celdas = crudo[["lat", "lon"]].drop_duplicates().to_numpy()
    series = {}
    with open(ORIGINALES / "peru_departamental.geojson", encoding="utf-8") as f:
        for x in json.load(f)["features"]:
            c = shape(x["geometry"]).representative_point()
            lat, lon = celdas[np.argmin((celdas[:, 0] - c.y) ** 2 + (celdas[:, 1] - c.x) ** 2)]
            d = crudo[(crudo["lat"] == lat) & (crudo["lon"] == lon)]
            series[NOMBRES[x["properties"]["NOMBDEP"]]] = d.groupby("anio", as_index=False).agg(t=("T2M", "mean"), ll=("lluvia_mm", "sum"))
    return series


def contraste_era5(ind):
    """ERA5 en un punto de cada departamento frente a NASA POWER en la misma zona."""
    from procesar_datos import NOMBRES
    if not (ORIGINALES / "era5_centroides.csv").exists():
        return None
    nasa = nasa_en_punto()
    e = pd.read_csv(ORIGINALES / "era5_centroides.csv")
    e["departamento"] = e["departamento"].map(NOMBRES)
    filas = []
    for dep, d in e.groupby("departamento"):
        filas.append({"departamento": dep, "tend_era5": tendencia(d["anio"], d["temperature_2m_mean"])["por_decada"],
                      "tend_nasa_celda": tendencia(nasa[dep]["anio"], nasa[dep]["t"])["por_decada"]})
    m = pd.DataFrame(filas).merge(ind[["departamento", "tend_temp"]], on="departamento")
    m.round(3).to_csv(PROCESADOS / "contraste_era5.csv", index=False)
    salida = {"departamentos": int(len(m)), "media_nasa_depto": m["tend_temp"].mean(), "media_nasa_celda": m["tend_nasa_celda"].mean(),
              "media_era5": m["tend_era5"].mean(), "era5_positivos": int((m["tend_era5"] > 0).sum()),
              "spearman_celda": stats.spearmanr(m["tend_nasa_celda"], m["tend_era5"]).statistic,
              "spearman_depto": stats.spearmanr(m["tend_temp"], m["tend_era5"]).statistic,
              "temp": m.round(3).to_dict("records")}
    g = e.groupby("anio", as_index=False)["temperature_2m_mean"].mean()
    t_g = tendencia(g["anio"], g["temperature_2m_mean"])
    salida["promedio_25_puntos"] = {"por_decada": t_g["por_decada"], "ic95": t_g["ic95"],
                                    "cambio_temp": periodo(g, P2)["temperature_2m_mean"].mean() - periodo(g, P1)["temperature_2m_mean"].mean(),
                                    "anios_mas_calidos": g.nlargest(3, "temperature_2m_mean")["anio"].astype(int).tolist()}
    salida["era5_significativos_positivos"] = int(sum(stats.kendalltau(d["anio"], d["temperature_2m_mean"]).pvalue < .05
                                                      and stats.linregress(d["anio"], d["temperature_2m_mean"]).slope > 0
                                                      for _, d in e.groupby("departamento")))
    ruta = ORIGINALES / "era5_lluvia_centroides.csv"
    if ruta.exists():
        ll = pd.read_csv(ruta)
        ll["departamento"] = ll["departamento"].map(NOMBRES)
        filas = []
        for dep, d in ll.groupby("departamento"):
            n = nasa[dep]
            camb = lambda x, c: 100 * (periodo(x, P2)[c].mean() / periodo(x, P1)[c].mean() - 1)
            filas.append({"departamento": dep, "cambio_era5_pct": camb(d, "precipitation_sum"), "cambio_nasa_celda_pct": camb(n, "ll"),
                          "lluvia_era5_p2": periodo(d, P2)["precipitation_sum"].mean(), "lluvia_nasa_celda_p2": periodo(n, P2)["ll"].mean()})
        l = pd.DataFrame(filas).merge(ind[["departamento", "cambio_lluvia_pct"]], on="departamento")
        l["mismo_signo"] = np.sign(l["cambio_era5_pct"]) == np.sign(l["cambio_lluvia_pct"])
        l.round(2).to_csv(PROCESADOS / "contraste_era5_lluvia.csv", index=False)
        salida["lluvia"] = l.round(2).to_dict("records")
        salida["lluvia_mismo_signo"] = int(l["mismo_signo"].sum())
        salida["lluvia_n"] = int(len(l))
        salida["spearman_lluvia"] = stats.spearmanr(l["cambio_era5_pct"], l["cambio_lluvia_pct"]).statistic
        salida["caida_ambas_10"] = sorted(l[(l["cambio_era5_pct"] <= -10) & (l["cambio_lluvia_pct"] <= -10)]["departamento"])
        salida["subida_ambas_10"] = sorted(l[(l["cambio_era5_pct"] >= 10) & (l["cambio_lluvia_pct"] >= 10)]["departamento"])
        # El primer periodo incluye los El Niño extremos: ¿la caída del norte depende de esos años?
        extremos = (1983, 1998, 2017, 2023)
        sens = {}
        anual = pd.read_csv(PROCESADOS / "anual_departamento.csv")
        for dep in salida["caida_ambas_10"]:
            sin_n = anual[(anual["departamento"] == dep) & ~anual["anio"].isin(extremos)]
            sin_e = ll[(ll["departamento"] == dep) & ~ll["anio"].isin(extremos)]
            sens[dep] = {"nasa_pct": 100 * (periodo(sin_n, P2)["lluvia_mm"].mean() / periodo(sin_n, P1)["lluvia_mm"].mean() - 1),
                         "era5_pct": 100 * (periodo(sin_e, P2)["precipitation_sum"].mean() / periodo(sin_e, P1)["precipitation_sum"].mean() - 1)}
        salida["norte_sin_anios_el_nino"] = sens
    return salida


def main():
    anual = pd.read_csv(PROCESADOS / "anual_departamento.csv")
    mensual = pd.read_csv(PROCESADOS / "mensual_departamento.csv")
    nacional = pd.read_csv(PROCESADOS / "anual_nacional.csv")
    nacional_m = pd.read_csv(PROCESADOS / "mensual_nacional.csv")
    celdas = pd.read_csv(PROCESADOS / "celdas.csv")
    altitud = celdas.groupby("departamento")["altitud_celda"].mean().round(0).to_dict()

    ind = indicadores(anual, altitud)
    ind.round(3).to_csv(PROCESADOS / "indicadores_departamento.csv", index=False)
    cel = tendencias_celdas()
    cel.round(4).to_csv(PROCESADOS / "tendencias_celdas.csv", index=False)

    tn = tendencia(nacional["anio"], nacional["temp_media"])
    a, b = periodo(nacional, P1), periodo(nacional, P2)
    base = periodo(nacional, BASE)["temp_media"].mean()
    nacional["anomalia"] = nacional["temp_media"] - base
    temporada = {}
    for mes, d in nacional_m.groupby("mes"):
        temporada[int(mes)] = {"tend_temp": tendencia(d["anio"], d["temp_media"])["por_decada"],
                               "cambio_lluvia_pct": 100 * (periodo(d, P2)["lluvia_mm"].mean() / periodo(d, P1)["lluvia_mm"].mean() - 1)}
    res = {"periodos": {"p1": P1, "p2": P2, "base": BASE},
           "nacional": {**tn, "cambio_temp": b["temp_media"].mean() - a["temp_media"].mean(),
                        "temp_p1": a["temp_media"].mean(), "temp_p2": b["temp_media"].mean(),
                        "cambio_max": b["temp_max"].mean() - a["temp_max"].mean(),
                        "cambio_min": b["temp_min"].mean() - a["temp_min"].mean(),
                        "lluvia_p1": a["lluvia_mm"].mean(), "lluvia_p2": b["lluvia_mm"].mean(),
                        "cambio_lluvia_pct": 100 * (b["lluvia_mm"].mean() / a["lluvia_mm"].mean() - 1),
                        "p_lluvia": stats.kendalltau(nacional["anio"], nacional["lluvia_mm"]).pvalue,
                        "anios_mas_calidos": nacional.nlargest(10, "anomalia")[["anio", "anomalia"]].round(3).to_dict("records"),
                        "anios_mas_frios": nacional.nsmallest(5, "anomalia")[["anio", "anomalia"]].round(3).to_dict("records")},
           "departamentos": {"tendencia_positiva": int((ind["tend_temp"] > 0).sum()),
                             "significativos_q05": int((ind["q_temp"] < .05).sum()),
                             "lluvia_baja": int((ind["cambio_lluvia_pct"] < 0).sum()),
                             "lluvia_sube": int((ind["cambio_lluvia_pct"] > 0).sum()),
                             "lluvia_significativos_q05": int((ind["q_lluvia"] < .05).sum())},
           "ranking_temp": ind[["departamento", "zona", "altitud_m", "tend_temp", "tend_temp_ic95", "tend_temp_sen", "q_temp", "cambio_temp"]].round(3).to_dict("records"),
           "ranking_lluvia": ind.sort_values("cambio_lluvia_pct")[["departamento", "lluvia_p1", "lluvia_p2", "cambio_lluvia_pct", "cambio_lluvia_mm", "tend_lluvia_pct", "p_lluvia", "q_lluvia"]].round(3).to_dict("records"),
           "zonas": ind.groupby("zona")[["tend_temp", "cambio_temp", "cambio_lluvia_pct", "tend_max", "tend_min"]].mean().round(3).to_dict("index"),
           "altitud_vs_tendencia": {"depto_spearman": stats.spearmanr(ind["altitud_m"], ind["tend_temp"]).statistic,
                                    "depto_p": stats.spearmanr(ind["altitud_m"], ind["tend_temp"]).pvalue,
                                    "celdas_spearman": stats.spearmanr(cel["altitud"], cel["tend_temp"]).statistic,
                                    "celdas_p": stats.spearmanr(cel["altitud"], cel["tend_temp"]).pvalue},
           "temporada": temporada, "era5": contraste_era5(ind),
           "celdas": {"n": int(len(cel)), "positivas": int((cel["tend_temp"] > 0).sum()),
                      "p10": cel["tend_temp"].quantile(.1), "p90": cel["tend_temp"].quantile(.9)}}
    (PROCESADOS / "resultados.json").write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float))

    WEB.mkdir(exist_ok=True)
    # El dashboard recalcula los indicadores en el navegador a partir de estos meses.
    deptos = sorted(anual["departamento"].unique())
    salida = {"anios": sorted(int(x) for x in anual["anio"].unique()), "departamentos": deptos,
              "zona": dict(zip(ind["departamento"], ind["zona"])), "altitud": altitud,
              "resultados": res, "control": json.loads((PROCESADOS / "control_calidad.json").read_text()),
              "serie": {}, "nacional": {}}
    for dep in deptos:
        d = mensual[mensual["departamento"] == dep].sort_values(["anio", "mes"])
        salida["serie"][dep] = {c: [round(float(x), 2) for x in d[c]] for c in ["temp_media", "temp_max", "temp_min", "lluvia_mm"]}
    d = nacional_m.sort_values(["anio", "mes"])
    salida["nacional"] = {c: [round(float(x), 2) for x in d[c]] for c in ["temp_media", "temp_max", "temp_min", "lluvia_mm"]}
    (WEB / "clima.json").write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":"), default=float))

    print(json.dumps({k: res[k] for k in ["nacional", "departamentos", "zonas", "altitud_vs_tendencia", "celdas"]}, indent=1, ensure_ascii=False, default=float))
    print(ind[["departamento", "zona", "altitud_m", "tend_temp", "tend_temp_ic95", "tend_temp_sen", "q_temp", "cambio_temp", "tend_max", "tend_min"]].round(2).to_string(index=False))
    print(ind.sort_values("cambio_lluvia_pct")[["departamento", "lluvia_p1", "lluvia_p2", "cambio_lluvia_pct", "tend_lluvia_pct", "p_lluvia", "q_lluvia"]].round(2).to_string(index=False))
    print(json.dumps(temporada, indent=0, default=float))
    if res["era5"]:
        print(json.dumps(res["era5"], indent=0, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
