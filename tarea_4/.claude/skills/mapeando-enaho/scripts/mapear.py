"""Mapa coroplético de la pobreza monetaria por departamento (ENAHO 2024), unido por código territorial.

    uv run .claude/skills/mapeando-enaho/scripts/mapear.py
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --indicador pobre_extremo

Lee salidas/personas_2024.parquet (de limpiando-enaho; si falta, termina con código 2) y el GeoJSON
departamental del curso (lo baja a datos/ si no está). Une ubigeo[:2] con FIRST_IDDP como texto y con
validate="one_to_one"; nunca por nombre. Exige 25 departamentos con dato, con Lima (15) y Callao (07) separados.

Salidas:
    mapas/pobreza_departamento.png                 el mapa (200 dpi)
    salidas/comparacion_mapa_referencia.csv       cada departamento frente a la referencia de la Sesión 16
    salidas/validacion_mapa.txt                    verificaciones de la unión y de la comparación
"""
import argparse
import sys
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "limpiando-enaho" / "scripts"))
from estimacion import por_grupo, raiz_proyecto  # noqa: E402

URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/"
               "lab/Data/peru_departamental_simple.geojson")
REFERENCIA = AQUI.parent / "referencias" / "pobreza_departamento_2024.csv"
INDICADORES = {"pobre": "Pobreza monetaria", "pobre_extremo": "Pobreza extrema"}
TOL_INEI = 0.1          # el método de la sumaria debe reproducir la referencia salvo redondeo
TOL_PERSONAS = 0.6      # base de personas: la población contada difiere (residentes vs mieperho); ver reference.md


def geometrias(datos):
    ruta = datos / "peru_departamental_simple.geojson"
    if not ruta.exists():
        print(f"Descargando {URL_GEOJSON} ...")
        datos.mkdir(parents=True, exist_ok=True)
        r = httpx.get(URL_GEOJSON, timeout=120)
        r.raise_for_status()
        ruta.write_bytes(r.content)
    g = gpd.read_file(ruta)
    g["FIRST_IDDP"] = g.FIRST_IDDP.astype(str).str.zfill(2)
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--indicador", default="pobre", choices=list(INDICADORES))
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--raiz", type=Path, default=raiz_proyecto(__file__))
    args = ap.parse_args()
    raiz = args.raiz
    base_path = raiz / "salidas" / f"personas_{args.anio}.parquet"
    if not base_path.exists():
        print(f"FALTA LA BASE: no existe {base_path.relative_to(raiz)}. Corran primero la skill limpiando-enaho "
              "(uv run .claude/skills/limpiando-enaho/scripts/limpiar.py).")
        sys.exit(2)
    base = pd.read_parquet(base_path)
    checks = []

    # 1. Indicador ponderado por departamento (ubigeo[:2])
    t = por_grupo(base, "departamento", y=args.indicador)
    t["departamento"] = t.departamento.astype(str).str.zfill(2)
    nombres = base.drop_duplicates("departamento").set_index("departamento").departamento_nombre
    t["nombre"] = t.departamento.map(nombres)

    # 2. Unión por código oficial, uno a uno
    g = geometrias(raiz / "datos")
    m = g.merge(t, left_on="FIRST_IDDP", right_on="departamento", how="left", validate="one_to_one")
    sin_dato = m[m.pct.isna()].NOMBDEP.tolist()
    checks.append(("Unidades territoriales en el GeoJSON", len(g), 25, len(g) == 25))
    checks.append(("Departamentos unidos con dato (ubigeo[:2] = FIRST_IDDP)", int(m.pct.notna().sum()), 25,
                   m.pct.notna().sum() == 25 and not sin_dato))
    checks.append(("Lima (15) y Callao (07) como unidades separadas",
                   ", ".join(sorted(m[m.FIRST_IDDP.isin(["07", "15"])].NOMBDEP)), "CALLAO, LIMA",
                   set(m[m.FIRST_IDDP.isin(["07", "15"])].departamento) == {"07", "15"}))
    if sin_dato or len(g) != 25:
        print(f"ERROR: la unión dejó departamentos sin dato: {sin_dato}. Revisen que los códigos sean texto "
              "de dos dígitos.")
        sys.exit(1)

    # 3. Comparación con la referencia de la Sesión 16 (solo pobreza monetaria)
    if args.indicador == "pobre":
        ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
        ind = pd.read_csv(raiz / "salidas" / "indicadores.csv", dtype={"codigo": str})
        inei = ind[ind.dimension == "departamento"].set_index("codigo").pobreza_pct_metodo_inei
        c = ref.rename(columns={"departamento": "nombre_referencia", "ccdd": "departamento", "pobreza_pct": "referencia"}) \
            .merge(t[["departamento", "nombre", "pct", "ic_inf", "ic_sup"]], on="departamento", validate="one_to_one")
        c["pct_metodo_inei"] = c.departamento.map(inei)
        c["dif_personas"] = (c.pct.round(1) - c.referencia).round(1)
        c["dif_metodo_inei"] = (c.pct_metodo_inei.round(1) - c.referencia).round(1)
        c["referencia_en_ic95"] = (c.referencia >= c.ic_inf) & (c.referencia <= c.ic_sup)
        c.to_csv(raiz / "salidas" / "comparacion_mapa_referencia.csv", index=False, float_format="%.4f")
        checks.append(("Máx. diferencia con la referencia, método INEI (sumaria)",
                       f"{c.dif_metodo_inei.abs().max():.1f} pp", f"<= {TOL_INEI} pp",
                       c.dif_metodo_inei.abs().max() <= TOL_INEI))
        checks.append(("Máx. diferencia con la referencia, base de personas (facpob07)",
                       f"{c.dif_personas.abs().max():.1f} pp ({c.loc[c.dif_personas.abs().idxmax(), 'nombre']})",
                       f"<= {TOL_PERSONAS} pp", c.dif_personas.abs().max() <= TOL_PERSONAS))
        checks.append(("Referencia dentro del IC 95 % de la estimación", f"{int(c.referencia_en_ic95.sum())}/25",
                       "25/25", c.referencia_en_ic95.all()))
        checks.append(("Mismo departamento con mayor y menor pobreza que la referencia",
                       f"{c.loc[c.pct.idxmax(), 'nombre']} / {c.loc[c.pct.idxmin(), 'nombre']}",
                       f"{c.loc[c.referencia.idxmax(), 'nombre']} / "
                       f"{c.loc[c.referencia.idxmin(), 'nombre']}",
                       c.pct.idxmax() == c.referencia.idxmax() and c.pct.idxmin() == c.referencia.idxmin()))

    # 4. Mapa: un solo tono de claro a oscuro, desde 0
    nombre_ind = INDICADORES[args.indicador]
    vmax = float(np.ceil(m.pct.max() / 10) * 10)
    fig, ax = plt.subplots(figsize=(7.5, 9.5))
    m.plot(column="pct", cmap="OrRd", vmin=0, vmax=vmax, linewidth=0.5, edgecolor="white", ax=ax, legend=True,
           legend_kwds={"label": f"{nombre_ind} (% de personas)", "shrink": 0.55, "orientation": "vertical"})
    pts = m.to_crs(32718).representative_point().to_crs(4326)
    for (_, fila), p in zip(m.iterrows(), pts):
        if fila.FIRST_IDDP == "07":                 # Callao es muy pequeño: etiqueta afuera con una línea
            ax.annotate(f"Callao {fila.pct:.1f}", (p.x, p.y), xytext=(p.x - 2.2, p.y - 0.6), fontsize=7,
                        arrowprops={"arrowstyle": "-", "color": "#333", "lw": 0.6})
            continue
        oscuro = fila.pct > 0.6 * vmax
        ax.text(p.x, p.y, f"{fila.pct:.1f}", ha="center", va="center", fontsize=7,
                color="white" if oscuro else "#222")
    ax.set_axis_off()
    top3 = m.nlargest(3, "pct")
    bot3 = m.nsmallest(3, "pct")
    titulo = f"{nombre_ind} por departamento, Perú {args.anio}"
    sub = (f"Más alta: {', '.join(f'{r.nombre} ({r.pct:.1f})' for r in top3.itertuples())}.\n"
           f"Más baja: {', '.join(f'{r.nombre} ({r.pct:.1f})' for r in bot3.itertuples())}. "
           "Cifras en % de personas.")
    fig.text(0.03, 0.97, titulo, fontsize=13, fontweight="bold", va="top")
    fig.text(0.03, 0.935, sub, fontsize=8.5, va="top", color="#333")
    fig.text(0.03, 0.02, f"Fuente: INEI, ENAHO {args.anio} (módulos 34 y 02), estimación ponderada con facpob07; "
             "límites departamentales del curso\n(GeoJSON, unido por ubigeo[:2] = FIRST_IDDP). Elaboración propia "
             "con limpiando-enaho y mapeando-enaho.", fontsize=7, color="#444")
    fig.subplots_adjust(top=0.9, bottom=0.06, left=0.02, right=0.98)
    (raiz / "mapas").mkdir(exist_ok=True)
    sufijo = "" if args.indicador == "pobre" else "_extrema"
    ruta = raiz / "mapas" / f"pobreza{sufijo}_departamento.png"
    fig.savefig(ruta, dpi=200)
    plt.close(fig)

    # 5. Reporte
    lineas = [f"VALIDACIÓN DEL MAPA · {nombre_ind}, ENAHO {args.anio}", f"Mapa: {ruta.relative_to(raiz)}", ""]
    for nombre, valor, ref, ok in checks:
        lineas.append(f"[{'OK' if ok else 'XX'}] {nombre}: {valor} (referencia: {ref}) "
                      f"{'APROBADA' if ok else 'FALLÓ'}")
    if args.indicador == "pobre":
        lineas += ["", "Comparación completa en salidas/comparacion_mapa_referencia.csv. La referencia del curso se "
                   "calculó con la sumaria (factor07 × mieperho); la base de personas cuenta a los residentes "
                   "habituales, por eso hay diferencias de algunas décimas, siempre dentro del IC 95 %."]
    texto = "\n".join(lineas)
    if args.indicador == "pobre":
        (raiz / "salidas" / "validacion_mapa.txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(m.sort_values("pct", ascending=False)[["FIRST_IDDP", "NOMBDEP", "pct", "ic_inf", "ic_sup"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
