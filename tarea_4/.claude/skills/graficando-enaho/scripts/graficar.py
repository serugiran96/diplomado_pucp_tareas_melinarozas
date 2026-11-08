"""Gráficos de pobreza de la ENAHO 2024 con estimaciones ponderadas e intervalos de confianza.

    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo area
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo departamento --indicador pobre_extremo
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --tipo todos

Tipos: area, sexo, sexo_jefe, edad, region, dominio, departamento, todos.
Lee salidas/personas_2024.parquet (la base de limpiando-enaho). Si no existe, termina con código 2 y pide
correr primero limpiando-enaho. Guarda PNG a 200 dpi en figuras/ y una tabla con las cifras graficadas en
salidas/figura_<tipo>.csv, para que cada número del gráfico se pueda rastrear.
"""
import argparse
import textwrap
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1] / "limpiando-enaho" / "scripts"))
from estimacion import por_grupo, proporcion, raiz_proyecto  # noqa: E402

COLOR = "#9c3d1b"
GRIS = "#6b6b6b"
TIPOS = {  # tipo: (columna, nombre del grupo, orden de las categorías o None para ordenar por valor)
    "area": ("area", "área de residencia", ["Urbana", "Rural"]),
    "sexo": ("sexo", "sexo", ["Hombre", "Mujer"]),
    "sexo_jefe": ("sexo_jefe", "sexo del jefe o jefa de hogar", ["Hombre", "Mujer"]),
    "edad": ("grupo_edad", "grupo de edad", ["0-14", "15-29", "30-44", "45-64", "65+"]),
    "region": ("region_natural", "región natural", None),
    "dominio": ("dominio_nombre", "dominio geográfico", None),
    "departamento": ("departamento_nombre", "departamento", None),
}
INDICADORES = {"pobre": "Pobreza monetaria", "pobre_extremo": "Pobreza extrema"}


FRASES = {("area", "Urbana"): "el área urbana", ("area", "Rural"): "el área rural",
          ("sexo", "Hombre"): "los hombres", ("sexo", "Mujer"): "las mujeres",
          ("sexo_jefe", "Hombre"): "los hogares con jefe hombre", ("sexo_jefe", "Mujer"): "los hogares con jefa mujer"}


def titulo_analitico(t, indicador, grupo, tipo):
    """Una frase que dice qué muestra el gráfico, con las cifras ya calculadas. Si la diferencia entre dos
    grupos no supera su margen de error (IC 95 %), lo dice en vez de exagerarla."""
    nombre = INDICADORES[indicador].lower()
    alto, bajo = t.iloc[t.pct.idxmax()], t.iloc[t.pct.idxmin()]
    if len(t) == 2:
        brecha = alto.pct - bajo.pct
        f_alto, f_bajo = FRASES.get((tipo, alto.categoria), alto.categoria), FRASES.get((tipo, bajo.categoria),
                                                                                        bajo.categoria)
        if brecha < 1.96 * (alto.ee ** 2 + bajo.ee ** 2) ** 0.5:
            return (f"La {nombre} es similar en {f_alto} ({alto.pct:.1f}\u00a0%) y {f_bajo} ({bajo.pct:.1f}\u00a0%): "
                    "la diferencia está dentro del margen de error")
        return (f"La {nombre} es {brecha:.1f} puntos mayor en {f_alto} ({alto.pct:.1f}\u00a0%) "
                f"que en {f_bajo} ({bajo.pct:.1f}\u00a0%)")
    razon = alto.pct / bajo.pct if bajo.pct else float("nan")
    et = (lambda c: f"{c} años") if tipo == "edad" else (lambda c: c)
    return (f"La {nombre} va de {bajo.pct:.1f}\u00a0% ({et(bajo.categoria)}) a {alto.pct:.1f}\u00a0% "
            f"({et(alto.categoria)}): {razon:.1f} veces más según {grupo}")


def graficar(base, tipo, indicador, figuras, salidas, anio):
    col, grupo, orden = TIPOS[tipo]
    t = por_grupo(base, col, y=indicador).rename(columns={col: "categoria"})
    t["categoria"] = t.categoria.astype(str)
    if orden:
        t = t.set_index("categoria").loc[orden].reset_index()
    else:
        t = t.sort_values("pct", ascending=True if tipo == "departamento" else False).reset_index(drop=True)
    nac = proporcion(base, indicador)
    horizontal = len(t) > 6

    alto_fig = 9 if tipo == "departamento" else 5.6
    fig, ax = plt.subplots(figsize=(8.5, alto_fig))
    pos = range(len(t))
    err = [t.pct - t.ic_inf, t.ic_sup - t.pct]
    if horizontal:
        ax.barh(pos, t.pct, color=COLOR, height=0.7)
        ax.errorbar(t.pct, pos, xerr=err, fmt="none", ecolor="#333", elinewidth=0.8, capsize=2)
        ax.set_yticks(list(pos), t.categoria, fontsize=9)
        ax.axvline(nac["pct"], color=GRIS, linestyle="--", linewidth=1)
        ax.text(nac["pct"], len(t) - 0.3, f" Perú: {nac['pct']:.1f} %", color=GRIS, fontsize=8.5, va="bottom")
        for i, (v, s) in enumerate(zip(t.pct, t.ic_sup)):
            ax.text(s + 0.6, i, f"{v:.1f}", va="center", fontsize=8.5)
        ax.set_xlim(0, max(t.ic_sup) * 1.12)
        ax.set_xlabel("% de personas", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    else:
        ax.bar(pos, t.pct, color=COLOR, width=0.6)
        ax.errorbar(pos, t.pct, yerr=err, fmt="none", ecolor="#333", elinewidth=0.8, capsize=3)
        ax.set_xticks(list(pos), t.categoria, fontsize=10)
        ax.axhline(nac["pct"], color=GRIS, linestyle="--", linewidth=1)
        ax.text(len(t) - 0.5, nac["pct"], f"Perú: {nac['pct']:.1f} %", color=GRIS, fontsize=8.5,
                ha="right", va="bottom")
        for i, v in enumerate(t.pct):                  # el valor va dentro de la barra, lejos del IC
            ax.text(i, v * 0.5, f"{v:.1f} %", ha="center", va="center", fontsize=11, fontweight="bold",
                    color="white")
        ax.set_ylim(0, max(t.ic_sup) * 1.12)
        ax.set_ylabel("% de personas", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)

    titulo = textwrap.fill(titulo_analitico(t, indicador, grupo, tipo), 78)
    sub = textwrap.fill(f"{INDICADORES[indicador]} según {grupo}, Perú {anio} (% de personas). Estimación "
                        "ponderada con facpob07; líneas negras: intervalo de confianza al 95 %.", 115)
    pulgada = 1 / alto_fig                              # una pulgada en coordenadas de la figura
    fig.text(0.02, 1 - 0.18 * pulgada, titulo, ha="left", va="top", fontsize=12, fontweight="bold")
    alto_titulo = 0.24 * (titulo.count("\n") + 1)
    fig.text(0.02, 1 - (0.25 + alto_titulo) * pulgada, sub, ha="left", va="top", fontsize=8.5, color="#333")
    fig.text(0.02, 0.15 * pulgada, f"Fuente: INEI, ENAHO {anio} (módulos 34 y 02). Elaboración propia con "
             "limpiando-enaho y graficando-enaho.", fontsize=7.5, color="#444")
    fig.tight_layout(rect=(0, 0.45 * pulgada, 1, 1 - (0.45 + alto_titulo + 0.18 * (sub.count("\n") + 1))
                           * pulgada))
    sufijo = "" if indicador == "pobre" else "_extrema"
    ruta = figuras / f"pobreza{sufijo}_{tipo}.png"
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    t.insert(0, "grupo", grupo)
    t.insert(0, "indicador", indicador)
    t.to_csv(salidas / f"figura_{tipo}{sufijo}.csv", index=False, float_format="%.4f")
    print(f"{ruta.relative_to(figuras.parent)}: {titulo_analitico(t, indicador, grupo, tipo)}")
    print(t[["categoria", "pct", "ic_inf", "ic_sup", "n"]].to_string(index=False))
    return ruta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tipo", default="area", choices=list(TIPOS) + ["todos"])
    ap.add_argument("--indicador", default="pobre", choices=list(INDICADORES))
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--raiz", type=Path, default=raiz_proyecto(__file__))
    args = ap.parse_args()
    base_path = args.raiz / "salidas" / f"personas_{args.anio}.parquet"
    if not base_path.exists():
        print(f"FALTA LA BASE: no existe {base_path.relative_to(args.raiz)}. Corran primero la skill "
              "limpiando-enaho (uv run .claude/skills/limpiando-enaho/scripts/limpiar.py).")
        sys.exit(2)
    base = pd.read_parquet(base_path)
    figuras, salidas = args.raiz / "figuras", args.raiz / "salidas"
    figuras.mkdir(exist_ok=True)
    for tipo in (TIPOS if args.tipo == "todos" else [args.tipo]):
        graficar(base, tipo, args.indicador, figuras, salidas, args.anio)


if __name__ == "__main__":
    main()
