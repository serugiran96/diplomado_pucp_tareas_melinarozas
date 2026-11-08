"""Limpia la ENAHO 2024 (módulos 34 y 02), arma la base de personas y valida contra el INEI.

    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py              # usa datos/966-Modulo34.zip y 02
    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --descargar  # baja los zip del INEI si faltan

Salidas (en la raíz del proyecto):
    salidas/personas_2024.parquet   residentes habituales con pobreza, área, departamento y factor (no va a git)
    salidas/indicadores.csv         pobreza ponderada por grupo, con error estándar e IC 95 % por diseño
    salidas/validacion.txt          cada verificación con su valor, la referencia y APROBADA / FALLÓ

Si falla una verificación esencial, el script termina con código 1, no guarda la base y lo dice en
validacion.txt. Nunca ajusta los resultados para que coincidan con la referencia.
"""
import argparse
import io
import sys
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from estimacion import por_grupo, proporcion, raiz_proyecto  # noqa: E402

CODIGO_INEI = {2024: 966}                      # código de la ENAHO anual en el portal de microdatos del INEI
URL_INEI = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LARGO_LLAVES = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Referencias publicadas (INEI, ENAHO 2024; Sesión 16 del curso). Solo se usan para comparar, nunca para ajustar.
REF = {"pobreza_nacional": 27.6, "residentes": 108_664, "departamentos": 25, "hogares": 33_691,
       "pobreza_urbana": 24.8, "pobreza_rural": 39.3, "pobreza_extrema": 5.5, "lima_metropolitana": 28.2}
TOLERANCIA_NACIONAL = 0.1                      # puntos porcentuales, según la consigna de la tarea

DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios",
    "18": "Moquegua", "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna",
    "24": "Tumbes", "25": "Ucayali"}
DOMINIOS = {1: "Costa norte", 2: "Costa centro", 3: "Costa sur", 4: "Sierra norte", 5: "Sierra centro",
            6: "Sierra sur", 7: "Selva", 8: "Lima Metropolitana"}
REGION_NATURAL = {1: "Costa", 2: "Costa", 3: "Costa", 8: "Costa", 4: "Sierra", 5: "Sierra", 6: "Sierra", 7: "Selva"}
GRUPOS_EDAD = [(0, 14, "0-14"), (15, 29, "15-29"), (30, 44, "30-44"), (45, 64, "45-64"), (65, 200, "65+")]

COLS_SUMARIA = LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "factor07", "mieperho", "linea",
                               "gashog2d", "inghog2d"]
COLS_MIEMBROS = LLAVES_HOGAR + ["codperso", "ubigeo", "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]


def normalizar(columnas):
    """Minúsculas, sin espacios ni tildes: 'aÑo' -> 'anio', 'P208A' -> 'p208a'."""
    def una(c):
        c = str(c).strip().lower().replace("ñ", "ni")
        return unicodedata.normalize("NFD", c).encode("ascii", "ignore").decode()
    return [una(c) for c in columnas]


def zip_modulo(datos, anio, modulo, descargar):
    codigo = CODIGO_INEI[anio]
    ruta = datos / f"{codigo}-Modulo{modulo}.zip"
    if not ruta.exists():
        url = URL_INEI.format(codigo=codigo, modulo=modulo)
        if not descargar:
            sys.exit(f"ERROR: falta {ruta}. Bájenlo de {url} (o corran este script con --descargar).")
        print(f"Descargando {url} ...")
        datos.mkdir(parents=True, exist_ok=True)
        r = httpx.get(url, timeout=300, follow_redirects=True)
        r.raise_for_status()
        ruta.write_bytes(r.content)
    return ruta


def leer_dta(ruta_zip, patron, columnas):
    """Lee el .dta del zip con las llaves como texto (sin perder ceros iniciales) y los nombres normalizados."""
    with zipfile.ZipFile(ruta_zip) as z:
        candidatos = [n for n in z.namelist() if n.lower().endswith(patron)]
        if len(candidatos) != 1:
            sys.exit(f"ERROR: en {ruta_zip.name} se esperaba un archivo *{patron} y hay {candidatos}.")
        df = pd.read_stata(io.BytesIO(z.read(candidatos[0])), convert_categoricals=False)
    df.columns = normalizar(df.columns)
    faltan = set(columnas) - set(df.columns)
    if faltan:
        sys.exit(f"ERROR: a {candidatos[0]} le faltan las columnas {sorted(faltan)}.")
    df = df[columnas].copy()
    for llave, largo in LARGO_LLAVES.items():
        if llave in df:
            df[llave] = df[llave].astype(str).str.strip().str.zfill(largo)
    return df, candidatos[0]


def metodo_inei(hog):
    """Pobreza con la sumaria y factor07 × mieperho (método de las cifras oficiales del INEI), en %.

    Devuelve un dict {(dimension, codigo): pct} para nacional, extrema, area, dominio y departamento. Sirve
    para contrastar; las cifras del proyecto se calculan con la base de personas y facpob07.
    """
    h = hog.assign(w=hog.factor07 * hog.mieperho, pobre=hog.pobreza.le(2), extremo=hog.pobreza.eq(1),
                   area=hog.estrato.le(5).map({True: "Urbana", False: "Rural"}),
                   departamento=hog.ubigeo.str[:2], dominio=hog.dominio.astype(str))
    pct = lambda d, y="pobre": round(100 * float((d.w * d[y]).sum() / d.w.sum()), 4)
    out = {("nacional", "PE"): pct(h), ("extrema", "PE"): pct(h, "extremo")}
    for dim in ("area", "dominio", "departamento"):
        for cat, g in h.groupby(dim):
            out[(dim, str(cat))] = pct(g)
    return out


class Validador:
    def __init__(self):
        self.filas = []

    def check(self, nombre, valor, referencia, ok, esencial=True, nota=""):
        self.filas.append({"verificacion": nombre, "valor": valor, "referencia": referencia,
                           "estado": "APROBADA" if ok else "FALLÓ", "esencial": esencial, "nota": nota})
        return ok

    @property
    def fallas_esenciales(self):
        return [f for f in self.filas if f["esencial"] and f["estado"] == "FALLÓ"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anio", type=int, default=2024, choices=sorted(CODIGO_INEI))
    ap.add_argument("--raiz", type=Path, default=raiz_proyecto(__file__), help="carpeta del proyecto")
    ap.add_argument("--descargar", action="store_true", help="baja los zip del INEI si no están en datos/")
    args = ap.parse_args()
    raiz, anio = args.raiz, args.anio
    datos, salidas = raiz / "datos", raiz / "salidas"
    salidas.mkdir(exist_ok=True)
    v = Validador()

    # 1. Leer
    z34 = zip_modulo(datos, anio, "34", args.descargar)
    z02 = zip_modulo(datos, anio, "02", args.descargar)
    hog, f34 = leer_dta(z34, f"sumaria-{anio}.dta", COLS_SUMARIA)
    per, f02 = leer_dta(z02, f"enaho01-{anio}-200.dta", COLS_MIEMBROS)
    print(f"Leídos {f34}: {len(hog):,} hogares y {f02}: {len(per):,} personas")

    # 2. Llaves: texto, con su largo y únicas
    for nombre, df, llaves in (("sumaria", hog, LLAVES_HOGAR), ("miembros", per, LLAVES_HOGAR + ["codperso"])):
        largos_ok = all((df[k].str.len() == LARGO_LLAVES[k]).all() for k in llaves)
        v.check(f"Llaves de {nombre} como texto con ceros iniciales ({', '.join(llaves)})",
                "sí" if largos_ok else "no", "sí", largos_ok)
        dup = int(df.duplicated(llaves).sum())
        v.check(f"Llaves únicas en {nombre}", f"{dup} duplicados", "0 duplicados", dup == 0)
    v.check("Hogares en la sumaria", f"{len(hog):,}", f"{REF['hogares']:,}", len(hog) == REF["hogares"])

    # 3. Residentes habituales: miembros presentes (p204 == 1) que no están ausentes 30 días o más (p205 == 2),
    #    más los no miembros (p204 == 2) que están presentes 30 días o más (p206 == 1)
    residente = ((per.p204 == 1) & (per.p205 == 2)) | ((per.p204 == 2) & (per.p206 == 1))
    res = per[residente].copy()
    v.check("Residentes habituales", f"{len(res):,}", f"{REF['residentes']:,}", len(res) == REF["residentes"],
            nota=f"de {len(per):,} filas del módulo 02")

    # 4. Unir personas (muchas) con su hogar (uno): validate="m:1" lanza error si un hogar se repite
    antes = len(res)
    base = res.merge(hog, on=LLAVES_HOGAR, how="left", validate="m:1", suffixes=("", "_hogar"), indicator=True)
    sin_hogar = int((base._merge != "both").sum())
    v.check("Unión m:1 sin duplicar filas", f"{antes:,} -> {len(base):,}", "igual número de filas",
            len(base) == antes)
    v.check("Todas las personas encuentran su hogar", f"{sin_hogar} sin hogar", "0", sin_hogar == 0)
    v.check("Persona única después de la unión", f"{int(base.duplicated(LLAVES_HOGAR + ['codperso']).sum())} "
            "duplicados", "0", not base.duplicated(LLAVES_HOGAR + ["codperso"]).any())
    ubigeo_igual = (base.ubigeo == base.ubigeo_hogar).mean()
    v.check("El ubigeo de la persona coincide con el del hogar", f"{ubigeo_igual:.2%}", "100 %",
            ubigeo_igual == 1, esencial=False)
    base = base.drop(columns=["_merge", "ubigeo_hogar"])

    # 5. Construir indicadores
    base["departamento"] = base.ubigeo.str[:2]
    base["departamento_nombre"] = base.departamento.map(DEPARTAMENTOS)
    base["area"] = base.estrato.le(5).map({True: "Urbana", False: "Rural"})
    base["pobre"] = base.pobreza.le(2).astype(int)
    base["pobre_extremo"] = base.pobreza.eq(1).astype(int)
    base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    base["edad"] = base.p208a
    base["grupo_edad"] = pd.cut(base.p208a, [g[0] - 1 for g in GRUPOS_EDAD] + [200],
                                labels=[g[2] for g in GRUPOS_EDAD]).astype(str)
    base["dominio_nombre"] = base.dominio.map(DOMINIOS)
    base["region_natural"] = base.dominio.map(REGION_NATURAL)
    jefes = base.loc[base.p203 == 1, LLAVES_HOGAR + ["sexo"]].rename(columns={"sexo": "sexo_jefe"})
    base = base.merge(jefes, on=LLAVES_HOGAR, how="left", validate="m:1")
    base["anio"] = anio

    codigos = sorted(base.departamento.unique())
    v.check("Códigos de departamento (ubigeo[:2])", f"{len(codigos)}: {codigos[0]}-{codigos[-1]}",
            "25: 01-25", codigos == sorted(DEPARTAMENTOS))
    v.check("Lima (15) y Callao (07) separados", "sí" if {"07", "15"} <= set(codigos) else "no", "sí",
            {"07", "15"} <= set(codigos))

    # 6. Factores de expansión
    nulos = int(base.facpob07.isna().sum() + (base.facpob07 <= 0).sum())
    v.check("facpob07 presente y positivo en todos los residentes", f"{nulos} nulos o <= 0", "0", nulos == 0)
    pob = base.facpob07.sum()
    v.check("Población expandida (suma de facpob07)", f"{pob:,.0f}", "≈ 34 millones (proyección INEI 2024)",
            33e6 < pob < 35.5e6)

    # 7. Pobreza: dos caminos independientes que deben coincidir
    nac = proporcion(base, "pobre")
    hog_pob = (hog.pobreza <= 2)
    pond_hog = hog.factor07 * hog.mieperho
    nac_hogares = round(100 * (pond_hog * hog_pob).sum() / pond_hog.sum(), 4)
    simple = round(100 * base.pobre.mean(), 4)
    v.check("Pobreza monetaria nacional (personas, facpob07)", f"{nac['pct']:.2f} %",
            f"{REF['pobreza_nacional']} % ± {TOLERANCIA_NACIONAL}",
            abs(nac["pct"] - REF["pobreza_nacional"]) <= TOLERANCIA_NACIONAL,
            nota=f"IC 95 %: {nac['ic_inf']:.2f}-{nac['ic_sup']:.2f}")
    v.check("Pobreza monetaria nacional (sumaria, factor07 × mieperho)", f"{nac_hogares:.2f} %",
            f"{REF['pobreza_nacional']} % ± {TOLERANCIA_NACIONAL}",
            abs(nac_hogares - REF["pobreza_nacional"]) <= TOLERANCIA_NACIONAL,
            nota="cálculo independiente con la sumaria: es el método oficial del INEI")
    v.check("El factor cambia el resultado (pobreza sin ponderar ≠ ponderada)", f"{simple:.2f} % sin ponderar",
            "distinta de la ponderada", abs(simple - nac["pct"]) > 0.5, esencial=False,
            nota="muestra por qué no se aceptan promedios simples")
    urb = proporcion(base, "pobre", dominio=base.area == "Urbana")
    rur = proporcion(base, "pobre", dominio=base.area == "Rural")
    ext = proporcion(base, "pobre_extremo")
    lim = proporcion(base, "pobre", dominio=base.dominio == 8)
    # Las referencias del INEI se calculan con la sumaria (factor07 × mieperho). Se muestran los dos métodos:
    # la diferencia viene de la población contada (residentes habituales del módulo 02 frente a mieperho).
    inei = metodo_inei(hog)
    for nombre, est, ref, clave in (("Pobreza urbana (estrato <= 5)", urb, "pobreza_urbana", ("area", "Urbana")),
                                    ("Pobreza rural (estrato >= 6)", rur, "pobreza_rural", ("area", "Rural")),
                                    ("Pobreza extrema nacional", ext, "pobreza_extrema", ("extrema", "PE")),
                                    ("Pobreza en Lima Metropolitana (dominio 8)", lim, "lima_metropolitana",
                                     ("dominio", "8"))):
        oficial = inei[clave]
        v.check(nombre, f"{est['pct']:.2f} % | {oficial:.2f} %", f"≈ {REF[ref]} %",
                abs(oficial - REF[ref]) <= 0.1, esencial=False,
                nota=f"personas+facpob07 | sumaria+factor07×mieperho; dif. entre métodos "
                     f"{est['pct'] - oficial:+.2f} pp")

    # 8. Indicadores por grupo
    tablas = [pd.DataFrame([{"dimension": "nacional", "codigo": "PE", "categoria": "Perú", **nac}])]
    for dim, col, nombres in (("area", "area", None), ("sexo", "sexo", None), ("sexo_jefe_hogar", "sexo_jefe", None),
                              ("grupo_edad", "grupo_edad", None), ("region_natural", "region_natural", None),
                              ("dominio", "dominio", DOMINIOS), ("departamento", "departamento", DEPARTAMENTOS)):
        t = por_grupo(base, col).rename(columns={col: "codigo"})
        t["codigo"] = t.codigo.astype(str)
        t["categoria"] = t.codigo.map(lambda c: (nombres or {}).get(int(c) if dim == "dominio" else c, c))
        t.insert(0, "dimension", dim)
        tablas.append(t)
    ext_tabla = pd.DataFrame([{"dimension": "pobreza_extrema_nacional", "codigo": "PE", "categoria": "Perú", **ext}])
    ind = pd.concat(tablas + [ext_tabla], ignore_index=True)
    ind["pobreza_pct_metodo_inei"] = [
        inei.get(("extrema", "PE") if d == "pobreza_extrema_nacional" else ("nacional", "PE") if d == "nacional"
                 else (d, c)) for d, c in zip(ind.dimension, ind.codigo)]
    ind = ind.rename(columns={"pct": "pobreza_pct", "n": "n_muestra", "poblacion": "poblacion_expandida"})
    ind.insert(0, "anio", anio)
    ind["indicador"] = ["pobreza_extrema" if d == "pobreza_extrema_nacional" else "pobreza_monetaria"
                        for d in ind.dimension]
    ind["fuente"] = f"INEI, ENAHO {anio} (módulos 34 y 02); cálculo propio ponderado con facpob07"
    v.check("Departamentos con estimación en indicadores.csv",
            str((ind.dimension == "departamento").sum()), "25", (ind.dimension == "departamento").sum() == 25)

    # 9. Escribir
    lineas = [f"VALIDACIÓN ENAHO {anio} · generado {datetime.now():%Y-%m-%d %H:%M}",
              f"Archivos: {z34.name}/{f34} y {z02.name}/{f02}",
              "Filtro de residentes: ((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))",
              "Unión: personas.merge(sumaria, on=[conglome, vivienda, hogar], validate='m:1')",
              "Pobreza: pobre = pobreza <= 2; ponderación con facpob07 (personas). Error estándar por diseño "
              "(conglome dentro de estrato).", ""]
    ancho = max(len(f["verificacion"]) for f in v.filas)
    for f in v.filas:
        marca = "[OK]" if f["estado"] == "APROBADA" else "[XX]"
        tipo = "esencial" if f["esencial"] else "informativa"
        lineas.append(f"{marca} {f['verificacion']:<{ancho}}  valor: {f['valor']:<22} referencia: "
                      f"{f['referencia']:<26} {f['estado']} ({tipo}){'  · ' + f['nota'] if f['nota'] else ''}")
    aprobadas = sum(f["estado"] == "APROBADA" for f in v.filas)
    lineas += ["", f"Resumen: {aprobadas}/{len(v.filas)} verificaciones aprobadas; "
               f"{len(v.fallas_esenciales)} esenciales fallidas."]
    if v.fallas_esenciales:
        lineas.append("RESULTADO: FALLÓ. No se guardó la base. Revisen las verificaciones marcadas con [XX].")
    else:
        lineas.append(f"RESULTADO: APROBADA. Base guardada en salidas/personas_{anio}.parquet "
                      f"({len(base):,} personas) e indicadores en salidas/indicadores.csv.")
    (salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))

    if v.fallas_esenciales:
        sys.exit(1)
    cols = LLAVES_HOGAR + ["codperso", "ubigeo", "departamento", "departamento_nombre", "dominio", "dominio_nombre",
                           "region_natural", "estrato", "area", "p203", "sexo", "sexo_jefe", "edad", "grupo_edad",
                           "pobreza", "pobre", "pobre_extremo", "facpob07", "factor07", "mieperho", "linea",
                           "gashog2d", "inghog2d", "anio"]
    base[cols].to_parquet(salidas / f"personas_{anio}.parquet", index=False)
    ind.to_csv(salidas / "indicadores.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
