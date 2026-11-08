"""Estimaciones ponderadas de la ENAHO con su error estándar por diseño muestral.

Lo usan las tres skills (limpiando, graficando y mapeando). Ninguna cifra se calcula con promedios simples:
toda proporción es sum(w * y) / sum(w) con el factor de expansión de personas (facpob07).

El error estándar sigue la linealización de Taylor para una razón, con conglomerados (conglome) dentro de
estratos (estrato), como `svyset conglome [pw=facpob07], strata(estrato)` en Stata. Para un subgrupo se
usan todos los conglomerados de la muestra (estimación por dominio), no solo los del subgrupo.
"""
import numpy as np
import pandas as pd

RAIZ_RELATIVA = 4          # scripts/ -> <skill>/ -> skills/ -> .claude/ -> raíz del proyecto
Z95 = 1.959964


def raiz_proyecto(archivo):
    """La carpeta del proyecto (la que tiene pyproject.toml), a partir de la ruta de un script de una skill."""
    from pathlib import Path
    p = Path(archivo).resolve()
    for padre in p.parents:
        if (padre / "pyproject.toml").exists() and (padre / ".claude").exists():
            return padre
    return p.parents[RAIZ_RELATIVA]


def proporcion(df, y, w="facpob07", dominio=None, estrato="estrato", psu="conglome"):
    """Proporción ponderada de la variable 0/1 `y` (en %) con error estándar e IC 95 % por diseño.

    dominio: máscara booleana del subgrupo (None = toda la población).
    Devuelve dict con pct, ee, ic_inf, ic_sup, cv_pct, n (personas en la muestra) y poblacion (expandida).
    """
    d = pd.Series(True, index=df.index) if dominio is None else dominio.astype(bool)
    wd = df[w].astype(float) * d
    W = wd.sum()
    if W == 0:
        raise ValueError("El subgrupo no tiene observaciones.")
    p = (wd * df[y]).sum() / W
    z = wd * (df[y] - p) / W                        # variable linealizada; 0 fuera del dominio
    por_psu = pd.DataFrame({"h": df[estrato].values, "c": df[psu].values, "z": z.values}) \
        .groupby(["h", "c"], observed=True).z.sum().reset_index()
    var = 0.0
    for _, g in por_psu.groupby("h"):
        n_h = len(g)
        if n_h > 1:
            var += n_h / (n_h - 1) * ((g.z - g.z.mean()) ** 2).sum()
    ee = float(np.sqrt(var))
    return {"pct": round(100 * p, 4), "ee": round(100 * ee, 4),
            "ic_inf": round(100 * (p - Z95 * ee), 4), "ic_sup": round(100 * (p + Z95 * ee), 4),
            "cv_pct": round(100 * ee / p, 2) if p else None,
            "n": int(d.sum()), "poblacion": round(float(W))}


def por_grupo(df, grupo, y="pobre", w="facpob07"):
    """Tabla con la proporción ponderada de `y` para cada categoría de `grupo`, ordenada por categoría."""
    filas = []
    for cat in sorted(df[grupo].dropna().unique()):
        filas.append({grupo: cat, **proporcion(df, y, w, dominio=df[grupo] == cat)})
    return pd.DataFrame(filas)
