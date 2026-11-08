"""Servidor MCP del BCRP para el agente de investigación socioeconómica (Tarea 4).

Parte del proyecto de la Sesión 04 (buscar_series, serie, resumen, recurso y prompt) y agrega herramientas propias:
comparar_periodos (la herramienta propia principal, con sus dos pruebas), graficar_serie, correlacion y
comparar_paises (Banco Mundial).

    uv run pytest                      # 8 pruebas originales + 2 de comparar_periodos = 10 passed
    uv run mcp/server.py               # el servidor, por stdio (Claude Code lo levanta solo con .mcp.json)

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import re
import time
import unicodedata
from datetime import date
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
RAIZ = AQUI.parent                                     # la carpeta tarea_4/
CATALOGO = RAIZ / "datos" / "bcrp" / "catalogo_bcrp.csv"
FIGURAS = RAIZ / "figuras"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, comparar_periodos para contrastar dos intervalos, "
    "serie para los datos y graficar_serie para guardar un gráfico. No calcules a mano: cita siempre el código "
    "de la serie, el periodo y la URL de la fuente que devuelve cada herramienta."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/bcrp/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes).map(_con_sinonimos)
    return df


# El catálogo dice lo mismo de varias formas: "var% 12 meses" en el IPC y "variación porcentual interanual" en el
# PBI. Se agregan los equivalentes al texto de búsqueda para que cualquiera de las dos formas encuentre la serie.
SINONIMOS = [("variacion porcentual interanual", "var% 12 meses interanual"),
             ("var% 12 meses", "interanual variacion porcentual"),
             ("variaciones porcentuales", "var% variacion porcentual"),
             ("variacion porcentual", "var%"),
             ("producto bruto interno", "pbi")]


def _con_sinonimos(texto):
    extra = [equivalente for frase, equivalente in SINONIMOS if frase in texto]
    return texto + (" " + " ".join(extra) if extra else "")


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio", "pbi var% 12 meses". frecuencia: "Diaria", "Mensual", "Trimestral"
    o "Anual". Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay
    resultados, prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes; luego aquellas cuyo nombre corto está formado solo por palabras pedidas (así
    # "pbi var% 12 meses" pone la serie llamada "PBI" antes que un sector); y, a igualdad, las de nombre más corto
    sel = df[m]
    palabras = set(_sin_tildes(texto).split())
    exacto = sel.nombre.map(lambda n: set(re.findall(r"[\w%]+", _sin_tildes(n))) <= palabras)
    orden = sel.assign(vieja=sel.actualizada < "2025", otro=~exacto, largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "otro", "largo"]).head(limite).codigo]


# ---------- serie ----------
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12}


def _partes(fecha):
    """'2025', '2025-01', '2025-1', '2025-T1' o '2025-01-15' -> (año, mes, día, trimestre); lo que falte es None."""
    m = re.fullmatch(r"(\d{4})(?:-(?:[Tt]([1-4])|(\d{1,2}))(?:-(\d{1,2}))?)?", str(fecha).strip())
    if not m:
        raise ToolError(f"Fecha {fecha!r} no válida. Usen '2025', '2025-01', '2025-T1' o '2025-01-15'.")
    anio, trim, mes, dia = m.groups()
    return int(anio), int(mes) if mes else None, int(dia) if dia else None, int(trim) if trim else None


def _fecha_api(fecha, frecuencia, fin):
    """Convierte una fecha al formato que pide la API según la frecuencia. fin=True completa hacia el final."""
    anio, mes, dia, trim = _partes(fecha)
    f = frecuencia.lower()
    if f == "anual":
        return f"{anio}"
    if f == "trimestral":
        t = trim or ((mes - 1) // 3 + 1 if mes else (4 if fin else 1))
        return f"{anio}-{t}"
    if trim:                                           # un trimestre pedido para una serie mensual o diaria
        mes = 3 * trim if fin else 3 * trim - 2
    mes = mes or (12 if fin else 1)
    if f == "mensual":
        return f"{anio}-{mes}"
    dia = dia or (pd.Period(f"{anio}-{mes:02d}").days_in_month if fin else 1)
    return f"{anio}-{mes:02d}-{dia:02d}"


def _siglo(aa, hasta):
    """La API da años de dos cifras en series diarias y trimestrales: el siglo sale del rango pedido."""
    anio = 2000 + int(aa)
    return anio if anio <= hasta else anio - 100


def _periodo(nombre, hasta):
    """'Ene.2025' -> '2025-01', '01.Oct.26' -> '2026-10-01', 'T1.25' -> '2025-T1', '2025' -> '2025'."""
    n = nombre.strip()
    if m := re.fullmatch(r"(\d{1,2})\.(\w{3})\.(\d{2})", n):
        return f"{_siglo(m[3], hasta)}-{MESES[m[2].lower()]:02d}-{int(m[1]):02d}"
    if m := re.fullmatch(r"(\w{3})\.(\d{4})", n):
        return f"{m[2]}-{MESES[m[1].lower()]:02d}"
    if m := re.fullmatch(r"T([1-4])\.(\d{2})", n):
        return f"{_siglo(m[2], hasta)}-T{m[1]}"
    if re.fullmatch(r"\d{4}", n):
        return n
    raise ValueError(f"Periodo desconocido: {nombre!r}")


@cache
def _descargar(url):
    """Baja una URL de la API. Si el BCRP limita los pedidos responde HTML: espera y reintenta."""
    for intento in range(5):
        try:
            r = httpx.get(url, timeout=30, follow_redirects=True)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                return r.json()
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(2 * (intento + 1))
    raise ToolError("El BCRP no respondió con datos. Esperen unos segundos y vuelvan a intentar.")


def _serie(codigo, desde, hasta):
    codigo = codigo.strip().upper()
    meta = _ficha(codigo)
    d, h = (_fecha_api(desde, meta["frecuencia"], False), _fecha_api(hasta, meta["frecuencia"], True))
    fuente = f"{API}/{codigo}/json/{d}/{h}"
    respuesta = _descargar(fuente)
    anio_hasta = _partes(hasta)[0]
    datos = []
    for p in respuesta.get("periods", []):
        valor = p["values"][0] if p.get("values") else "n.d."
        try:
            datos.append({"periodo": _periodo(p["name"], anio_hasta), "valor": round(float(valor), 4)})
        except ValueError:                             # "n.d." y similares: no hay dato ese periodo
            continue
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}. Empieza en {meta['inicio']}.")
    return {"codigo": codigo, "nombre": meta["nombre"], "frecuencia": meta["frecuencia"],
            "unidad": respuesta.get("config", {}).get("title", ""), "datos": datos, "fuente": fuente}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Datos de una serie del BCRP entre dos fechas, ambas incluidas. Úsala después de buscar_series.

    Fechas: "2025-01" (mensual), "2025-T1" (trimestral), "2025" (anual), "2026-10-15" (diaria).
    Para un solo dato, pongan la misma fecha en desde y hasta. Devuelve los periodos como "2025-01",
    "2026-10-01", "2025-T1" o "2025", sin los días sin dato, y la URL de la fuente para citarla.
    Ejemplo: serie("PN01273PM", "2026-01", "2026-09") -> inflación de Lima a 12 meses de enero a setiembre de 2026.
    """
    return _serie(codigo, desde, hasta)


# ---------- resumen ----------
NOTA_TASA = ("La serie ya es una tasa (variación %): el cambio está en puntos porcentuales y no se calcula "
             "la variación % de una tasa, que no tiene sentido económico.")


def _es_tasa(nombre):
    """True si la serie ya es una variación porcentual (inflación, crecimiento del PBI...)."""
    return bool(re.search(r"var\s*%|variaci[oó]n", nombre, re.IGNORECASE))


def _estadisticas(datos, tasa=False):
    """Primero, último, cambio, variación %, promedio, máximo y mínimo de una lista [{periodo, valor}].

    Si tasa=True (la serie ya es una variación %), variacion_pct es None y se agrega una nota.
    """
    df = pd.DataFrame(datos)
    primero, ultimo = float(df.valor.iloc[0]), float(df.valor.iloc[-1])
    punto = lambda i: {"periodo": df.periodo[i], "valor": float(df.valor[i])}
    r = {"n": len(df), "primero": punto(0), "ultimo": punto(len(df) - 1),
         "cambio": round(ultimo - primero, 4),
         "variacion_pct": None if tasa or not primero else round((ultimo / primero - 1) * 100, 4),
         "promedio": round(float(df.valor.mean()), 4),
         "maximo": punto(df.valor.idxmax()), "minimo": punto(df.valor.idxmin())}
    if tasa:
        r["nota"] = NOTA_TASA
    return r


@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Primero, último, cambio, variación %, promedio, máximo y mínimo de una serie entre dos fechas.

    Úsenla en vez de hacer cuentas a mano: para "cuánto subió", "cuál fue el promedio" o "cuándo fue el máximo".
    Mismas fechas que serie. cambio = último - primero; variacion_pct = (último / primero - 1) × 100.
    Si la serie ya es una variación % (inflación, crecimiento del PBI), el cambio está en puntos porcentuales
    y variacion_pct es None: la variación % de una tasa no tiene sentido económico.
    """
    s = _serie(codigo, desde, hasta)
    return {"codigo": s["codigo"], "nombre": s["nombre"], "frecuencia": s["frecuencia"],
            **_estadisticas(s["datos"], _es_tasa(s["nombre"])), "fuente": s["fuente"]}


# ---------- herramienta propia principal: comparar_periodos ----------
def _orden(fecha):
    """Clave para comparar fechas de cualquier frecuencia: (año, mes inicial, día)."""
    anio, mes, dia, trim = _partes(fecha)
    return anio, mes or (3 * trim - 2 if trim else 1), dia or 1


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_periodos(codigo: str, desde_a: str, hasta_a: str, desde_b: str, hasta_b: str) -> dict:
    """Compara el comportamiento de UNA serie del BCRP entre dos intervalos (A y B): promedio, extremos y cambio
    dentro de cada uno, y la diferencia entre ambos.

    Úsenla para preguntas como "¿la inflación de 2023-2024 fue menor que la de 2021-2022?" o "¿el PBI creció
    más antes o después de la pandemia?". Mismas fechas que serie. Devuelve:
    - periodo_a y periodo_b: n, primero, último, cambio, variación %, promedio, máximo y mínimo de cada intervalo;
    - diferencia_promedios = promedio B - promedio A (en las unidades de la serie; si la serie es una
      variación %, la diferencia está en puntos porcentuales);
    - variacion_pct_promedios = (promedio B / promedio A - 1) × 100 (None si la serie ya es una tasa);
    - mayor_promedio: "A", "B" o "iguales";
    - las dos URL de la fuente. Los intervalos pueden tener distinta duración, pero cada uno debe ir de
      desde a hasta (desde <= hasta).
    """
    for nombre, d, h in (("A", desde_a, hasta_a), ("B", desde_b, hasta_b)):
        if _orden(d) > _orden(h):
            raise ToolError(f"En el periodo {nombre}, desde ({d}) es posterior a hasta ({h}).")
    a, b = _serie(codigo, desde_a, hasta_a), _serie(codigo, desde_b, hasta_b)
    tasa = _es_tasa(a["nombre"])
    ea, eb = _estadisticas(a["datos"], tasa), _estadisticas(b["datos"], tasa)
    ea.pop("nota", None), eb.pop("nota", None)
    dif = round(eb["promedio"] - ea["promedio"], 4)
    return {"codigo": a["codigo"], "nombre": a["nombre"], "frecuencia": a["frecuencia"], "unidad": a["unidad"],
            "periodo_a": {"desde": a["datos"][0]["periodo"], "hasta": a["datos"][-1]["periodo"], **ea},
            "periodo_b": {"desde": b["datos"][0]["periodo"], "hasta": b["datos"][-1]["periodo"], **eb},
            "diferencia_promedios": dif,
            "unidad_diferencia": "puntos porcentuales" if tasa else "unidades de la serie",
            "variacion_pct_promedios": (round((eb["promedio"] / ea["promedio"] - 1) * 100, 4)
                                        if ea["promedio"] and not tasa else None),
            "mayor_promedio": "iguales" if dif == 0 else ("B" if dif > 0 else "A"),
            **({"nota": NOTA_TASA} if tasa else {}),
            "fuentes": [a["fuente"], b["fuente"]]}


# ---------- herramientas propias adicionales ----------
def _fechas(periodos):
    """'2025-01', '2025-T1', '2025' o '2026-10-01' -> fechas para el eje x de un gráfico."""
    def una(p):
        if "-T" in p:
            return pd.Period(p.replace("-T", "Q"), freq="Q").to_timestamp()
        if len(p) == 4:
            return pd.Timestamp(f"{p}-01-01")
        return pd.Timestamp(p if len(p) == 10 else f"{p}-01")
    return [una(p) for p in periodos]


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def graficar_serie(codigos: list[str], desde: str, hasta: str, titulo: str = "", archivo: str = "") -> dict:
    """Guarda en figuras/ un gráfico de líneas (PNG, 200 dpi) de una o varias series del BCRP y devuelve su ruta.

    Úsenla cuando pidan un gráfico de un indicador macro (inflación, PBI, tipo de cambio...). codigos: una lista
    como ["PN01273PM"] o ["PN01273PM", "PN01271PM"]; pongan varias solo si comparten unidad. Mismas fechas que
    serie. titulo: una frase analítica que diga qué muestra (si se omite, va el nombre de la serie).
    archivo: nombre del PNG (por defecto bcrp_<codigos>_<desde>_<hasta>.png). El gráfico lleva unidad,
    periodo y la nota «Fuente: BCRP» con los códigos. Devuelve la ruta, los puntos graficados y las fuentes.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if isinstance(codigos, str):
        codigos = [c for c in re.split(r"[,; ]+", codigos) if c]
    if not codigos or len(codigos) > 4:
        raise ToolError("Pasen entre 1 y 4 códigos de serie.")
    series = [_serie(c, desde, hasta) for c in codigos]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for s in series:
        df = pd.DataFrame(s["datos"])
        x = list(_fechas(df.periodo))
        etiqueta = f"{s['nombre']} ({s['codigo']})"
        ax.plot(x, df.valor, linewidth=2, label=etiqueta[:90])
        ax.annotate(f"{df.valor.iloc[-1]:.2f}", (x[-1], df.valor.iloc[-1]), textcoords="offset points",
                    xytext=(4, 0), va="center", fontsize=9)
    unidad = series[0]["unidad"] or series[0]["nombre"]
    entre_parentesis = re.findall(r"\(([^()]+)\)", unidad)
    if _es_tasa(series[0]["nombre"]):
        eje = "Variación porcentual (%)"
    elif entre_parentesis:
        eje = entre_parentesis[-1]                     # p. ej. "S/ por US$" o "índice 2007 = 100"
    else:
        eje = unidad if len(unidad) <= 45 else unidad[:44] + "…"
    ax.set_title(titulo or series[0]["nombre"], fontsize=12, loc="left", fontweight="bold")
    ax.set_ylabel(eje, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    if min(min(p["valor"] for p in s["datos"]) for s in series) < 0:
        ax.axhline(0, color="black", linewidth=0.8)
    if len(series) > 1:
        ax.legend(fontsize=8, frameon=False)
    if all(s["frecuencia"].lower() == "anual" for s in series):   # datos anuales: una marca por año, sin meses
        import matplotlib.dates as mdates
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    nota = (f"Fuente: BCRP, estadisticas.bcrp.gob.pe, series {', '.join(s['codigo'] for s in series)}. "
            f"Periodo {series[0]['datos'][0]['periodo']} a {series[0]['datos'][-1]['periodo']}. "
            f"Consultado el {date.today():%d/%m/%Y}.")
    fig.text(0.01, 0.01, nota, fontsize=7.5, color="#444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    FIGURAS.mkdir(exist_ok=True)
    nombre = archivo or f"bcrp_{'_'.join(s['codigo'] for s in series)}_{desde}_{hasta}.png"
    ruta = FIGURAS / Path(nombre).name
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return {"archivo": str(ruta.relative_to(RAIZ)), "series": [s["codigo"] for s in series],
            "puntos": sum(len(s["datos"]) for s in series), "unidad": unidad,
            "fuentes": [s["fuente"] for s in series]}


@mcp.tool(annotations=SOLO_LECTURA)
def correlacion(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Correlación de Pearson entre dos series del BCRP de la misma frecuencia, en los periodos que comparten.

    Úsenla para "¿se mueven juntos el cobre y el tipo de cambio?" o "¿la tasa de referencia sigue a la inflación?".
    Mismas fechas que serie. Va de -1 a 1; correlación no es causalidad.
    """
    a, b = _serie(codigo_a, desde, hasta), _serie(codigo_b, desde, hasta)
    df = pd.DataFrame(a["datos"]).merge(pd.DataFrame(b["datos"]), on="periodo", suffixes=("_a", "_b"))
    if len(df) < 3:
        raise ToolError("Hay menos de 3 periodos en común: revisen que las dos series tengan la misma frecuencia.")
    r = df.valor_a.corr(df.valor_b)
    return {"serie_a": {"codigo": a["codigo"], "nombre": a["nombre"]},
            "serie_b": {"codigo": b["codigo"], "nombre": b["nombre"]},
            "periodos": len(df), "desde": df.periodo.iloc[0], "hasta": df.periodo.iloc[-1],
            "correlacion": round(float(r), 4), "fuentes": [a["fuente"], b["fuente"]]}


BANCO_MUNDIAL = "https://api.worldbank.org/v2/country"
INDICADORES = {"crecimiento_pbi": "NY.GDP.MKTP.KD.ZG", "inflacion": "FP.CPI.TOTL.ZG",
               "pbi_per_capita": "NY.GDP.PCAP.CD", "desempleo": "SL.UEM.TOTL.ZS",
               "exportaciones_pct_pbi": "NE.EXP.GNFS.ZS", "deuda_publica_pct_pbi": "GC.DOD.TOTL.GD.ZS"}


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_paises(indicador: str = "crecimiento_pbi", paises: str = "PER,CHL,COL,MEX,BRA",
                    desde: int = 2015, hasta: int = 2025) -> dict:
    """Compara al Perú con otros países con datos anuales del Banco Mundial. El BCRP solo tiene datos del Perú:
    úsenla cuando la pregunta compara países ("¿creció Perú más que Chile?", "¿qué país tuvo más inflación?").

    indicador: crecimiento_pbi (%), inflacion (% anual, IPC), pbi_per_capita (US$ corrientes), desempleo (%),
    exportaciones_pct_pbi, deuda_publica_pct_pbi, o un código del Banco Mundial como "NY.GDP.MKTP.KD.ZG".
    paises: códigos ISO de 3 letras separados por comas, por ejemplo "PER,CHL,COL".
    Devuelve una tabla por año, el promedio de cada país en el periodo y la URL de la fuente.
    """
    codigo = INDICADORES.get(indicador.strip().lower(), indicador.strip())
    lista = [p.strip().upper() for p in re.split(r"[,; ]+", paises) if p.strip()]
    fuente = f"{BANCO_MUNDIAL}/{';'.join(lista)}/indicator/{codigo}?format=json&date={desde}:{hasta}&per_page=2000"
    try:
        r = httpx.get(fuente, timeout=30)
        cuerpo = r.json()
    except (httpx.HTTPError, ValueError):
        raise ToolError("El Banco Mundial no respondió. Vuelvan a intentar en unos segundos.")
    if len(cuerpo) < 2 or not cuerpo[1]:
        raise ToolError(f"Sin datos para {codigo!r} en {lista}. Revisen el indicador y los códigos ISO de 3 letras.")
    filas = [{"pais": x["countryiso3code"], "anio": int(x["date"]), "valor": round(x["value"], 4)}
             for x in cuerpo[1] if x["value"] is not None]
    df = pd.DataFrame(filas)
    tabla = df.pivot(index="anio", columns="pais", values="valor").sort_index()
    return {"indicador": cuerpo[1][0]["indicator"]["value"], "codigo": codigo,
            "por_anio": [{"anio": int(a), **{p: float(v) for p, v in fila.items() if pd.notna(v)}}
                         for a, fila in tabla.iterrows()],
            "promedio": {p: round(float(v), 4) for p, v in df.groupby("pais").valor.mean().items()},
            "fuente": fuente.replace("&per_page=2000", "")}


# ---------- recursos ----------
@mcp.resource("bcrp://serie/{codigo}")
def ficha(codigo: str) -> dict:
    """Ficha de una serie del BCRP: nombre, categoría, frecuencia, desde cuándo hay datos y última actualización."""
    return _ficha(codigo.strip().upper())


SERIES_CLAVE = {
    "PN01273PM": "Inflación de Lima Metropolitana, variación % del IPC en 12 meses (mensual)",
    "PN01271PM": "Inflación de Lima Metropolitana, variación % mensual del IPC (mensual)",
    "PM05197PA": "Inflación anual del IPC de Lima Metropolitana, variación % fin de periodo, dic/dic (anual)",
    "PM05217PA": "Inflación anual del IPC de Lima Metropolitana, variación % del índice promedio (anual)",
    "PN09822PM": "Inflación de alimentos y bebidas en Lima Metropolitana, variación % en 12 meses (mensual)",
    "PN01728AM": "PBI real, variación % interanual (respecto al mismo mes del año anterior) (mensual)",
    "PM04923AA": "PBI real, variación % anual (anual)",
    "PD04722MM": "Tasa de referencia de la política monetaria, % (mensual)",
    "PN01206PM": "Tipo de cambio interbancario venta, promedio del mes, S/ por US$ (mensual)",
    "PD04638PD": "Tipo de cambio interbancario venta, S/ por US$ (diaria)",
}


@mcp.resource("bcrp://series-clave")
def series_clave() -> dict:
    """Códigos de las series del BCRP más usadas en este proyecto, con lo que mide cada una. Es un punto de
    partida: confirmen siempre el nombre oficial con buscar_series o el recurso bcrp://serie/{codigo}."""
    return {"series": [{"codigo": c, "descripcion": d} for c, d in SERIES_CLAVE.items()],
            "fuente": "https://estadisticas.bcrp.gob.pe/estadisticas/series/"}


# ---------- prompts ----------
@mcp.prompt
def informe(tema: str) -> str:
    """Informe corto sobre un tema económico del Perú, con cifras verificables del BCRP."""
    return (f"Escribe un informe de 5 viñetas sobre «{tema}» en el Perú con datos oficiales del BCRP.\n"
            "1. Busca las series con buscar_series.\n"
            "2. Usa resumen o comparar_periodos para variaciones, promedios y extremos; no hagas cuentas a mano.\n"
            "3. En cada viñeta cita el código de la serie y el periodo, por ejemplo (PN01273PM, 2026-09).\n"
            "4. Si comparas con otros países, usa comparar_paises y cita el Banco Mundial.\n"
            "Termina con una línea de fuentes con las URLs que devolvieron las herramientas.")


@mcp.prompt
def interpretar_indicador(codigo: str, desde: str, hasta: str) -> str:
    """Interpreta un indicador del BCRP en un periodo: qué mide, cómo evolucionó y qué no se puede concluir."""
    return (f"Interpreta la serie {codigo} del BCRP entre {desde} y {hasta}.\n"
            f"1. Lee la ficha con el recurso bcrp://serie/{codigo} y di qué mide y en qué unidad.\n"
            "2. Llama a resumen y describe el punto de partida, el final, el máximo y el mínimo, con su periodo.\n"
            "3. Si el periodo es largo, usa comparar_periodos para contrastar la primera y la segunda mitad.\n"
            "4. Explica el patrón en lenguaje claro, sin atribuir causas que los datos no muestran.\n"
            "5. Cierra con la URL de la fuente que devolvieron las herramientas.")


@mcp.prompt
def investigacion_socioeconomica(pregunta: str) -> str:
    """Plan para responder una pregunta que combina el BCRP (MCP) con la ENAHO 2024 (Skills del proyecto)."""
    return (f"Pregunta de investigación: «{pregunta}»\n"
            "1. Escribe un plan corto: qué parte responde el BCRP y qué parte responde la ENAHO 2024.\n"
            "2. BCRP: busca las series con buscar_series, resume con resumen o comparar_periodos y guarda un "
            "gráfico con graficar_serie. Cita código, periodo y URL.\n"
            "3. ENAHO: usa las skills limpiando-enaho, graficando-enaho y mapeando-enaho; toda cifra va ponderada "
            "y sale de salidas/indicadores.csv o de los scripts.\n"
            "4. Si una herramienta falla o no hay datos, dilo; no inventes cifras.\n"
            "5. Las series del BCRP son nacionales o de Lima y la ENAHO es de hogares: describe asociaciones, "
            "no causas, y explica esa diferencia de nivel en las limitaciones.")


if __name__ == "__main__":
    mcp.run()
