"""Experimento: las mismas 10 preguntas en modo A (sin MCP ni Skills) y modo B (con MCP y Skills).

    uv run evaluacion/evaluar.py correr      # 20 sesiones independientes de claude -p (o: correr A / correr B)
    uv run evaluacion/evaluar.py calificar   # compara con las respuestas esperadas y escribe resultados.csv

Las respuestas esperadas y las tolerancias están en evaluacion/preguntas.csv desde antes de correr el
experimento (y se confirmaron con evaluacion/verificar_esperadas.py). Este script no las modifica.

Para las dos preguntas mixtas, además de las cifras se exige un criterio de interpretación (columna
criterio_interpretacion). Ese criterio se revisa leyendo cada respuesta y se anota en
evaluacion/revision_interpretacion.csv (modo, id, cumple, nota); calificar lo lee de ahí.
"""
import json
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
from claude_headless import HERRAMIENTAS_B, HERRAMIENTAS_GENERALES, MODELO, correr, leer, transcribir  # noqa: E402

INSTRUCCIONES = (
    "Responde en español. Da la cifra pedida con su unidad, el periodo y la fuente que usaste. No inventes datos: "
    "si no puedes obtener o verificar una cifra, dilo. Termina siempre con una última línea con el formato "
    "`RESPUESTA: valor1; valor2; ...` con los valores pedidos en el orden de la pregunta (números con punto "
    "decimal y sin el signo %, meses como AAAA-MM, respuestas de sí o no como sí o no). Si no tienes un valor, "
    "escribe NO DISPONIBLE en su lugar.")
EVID = RAIZ / "evidencias_ia" / "evaluacion"
CRUDO = AQUI / "crudo"
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
         "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
         "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "set": 9,
         "oct": 10, "nov": 11, "dic": 12}


def _norm(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode().strip(" .*`")


def correr_todo(modos=("A", "B"), trabajadores_a=3, trabajadores_b=2):
    preg = pd.read_csv(AQUI / "preguntas.csv")
    CRUDO.mkdir(exist_ok=True)

    def una(args):
        modo, fila = args
        jsonl = EVID / f"modo_{modo}" / f"{fila.id}.jsonl"
        r = correr(fila.pregunta, modo, jsonl, instrucciones=INSTRUCCIONES, timeout=900)
        transcribir(jsonl, jsonl.with_suffix(".md"), f"Evaluación · modo {modo} · {fila.id}", fila.pregunta, modo,
                    INSTRUCCIONES)
        r.update({"id": fila.id})
        (CRUDO / f"{modo}_{fila.id}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{modo}] {fila.id}: {r['segundos']} s, herramientas={sorted(set(r['herramientas']))}, "
              f"error={r['error'] or '-'}", flush=True)
        return r

    filas = list(preg.itertuples())
    with ThreadPoolExecutor(trabajadores_a) as ex_a, ThreadPoolExecutor(trabajadores_b) as ex_b:
        fa = [ex_a.submit(una, ("A", f)) for f in filas] if "A" in modos else []
        fb = [ex_b.submit(una, ("B", f)) for f in filas] if "B" in modos else []
        for f in fa + fb:
            f.result()


def linea_respuesta(texto):
    """La última línea 'RESPUESTA: ...' (con o sin negritas). None si el agente no la escribió."""
    m = re.findall(r"^\W*RESPUESTA\W*:\s*(.+)$", texto or "", flags=re.IGNORECASE | re.MULTILINE)
    return m[-1].strip(" *`") if m else None


def _numero(s):
    m = re.search(r"-?\d+(?:[.,]\d+)?", s.replace(" ", ""))
    return float(m.group().replace(",", ".")) if m else None


def _mes(s):
    s = _norm(s)
    if m := re.search(r"(\d{4})-(\d{1,2})", s):
        return f"{m[1]}-{int(m[2]):02d}"
    for nombre, n in sorted(MESES.items(), key=lambda x: -len(x[0])):
        if nombre in s and (a := re.search(r"(\d{4})", s)):
            return f"{a[1]}-{n:02d}"
    return None


def comparar(valores, esperados, tolerancias, unidades):
    """Devuelve (correcto, detalle) comparando cada valor con su esperado y tolerancia."""
    detalle = []
    if valores is None:
        return False, "sin línea RESPUESTA"
    partes = [p.strip() for p in valores.split(";")]
    ok = True
    for i, (e, t, u) in enumerate(zip(esperados, tolerancias, unidades)):
        v = partes[i] if i < len(partes) else ""
        if not v or "no disponible" in _norm(v):
            detalle.append(f"{e}: no disponible")
            ok = False
            continue
        if u == "mes":
            bien = _mes(v) == e
        elif u in ("texto", "sí/no"):
            bien = _norm(e) == _norm(v).split()[0] if _norm(v) else False
        else:
            n = _numero(v)
            bien = n is not None and abs(n - float(e)) <= float(t) + 1e-9   # 1e-9: solo precisión de punto flotante
        detalle.append(f"{e} vs {v}: {'ok' if bien else 'fuera de tolerancia'}")
        ok &= bien
    return ok, " | ".join(detalle)


def fuentes_citadas(texto, jsonl):
    """Fuentes que la respuesta menciona y dominios que el agente consultó en la web."""
    t = _norm(texto)
    claves = {"BCRP": "bcrp" in t or "banco central" in t, "INEI": "inei" in t, "ENAHO": "enaho" in t,
              "Banco Mundial": "banco mundial" in t or "world bank" in t}
    citadas = [k for k, v in claves.items() if v]
    dominios = set()
    for linea in Path(jsonl).read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "assistant":
            for b in d["message"].get("content", []):
                if b.get("type") == "tool_use" and b["name"] in ("WebFetch", "WebSearch"):
                    url = b["input"].get("url") or b["input"].get("query", "")
                    if m := re.search(r"https?://([^/\s]+)", url):
                        dominios.add(m[1])
                    elif b["name"] == "WebSearch":
                        dominios.add("búsqueda web")
    return ", ".join(citadas + sorted(dominios)) or "ninguna"


def calificar():
    preg = pd.read_csv(AQUI / "preguntas.csv").set_index("id")
    rev_path = AQUI / "revision_interpretacion.csv"
    rev = pd.read_csv(rev_path).set_index(["modo", "id"]) if rev_path.exists() else pd.DataFrame()
    filas = []
    for modo in ("A", "B"):
        for pid, p in preg.iterrows():
            jsonl = EVID / f"modo_{modo}" / f"{pid}.jsonl"
            crudo = CRUDO / f"{modo}_{pid}.json"
            if not jsonl.exists():
                continue
            r = json.loads(crudo.read_text(encoding="utf-8")) if crudo.exists() else leer(jsonl)
            valores = linea_respuesta(r.get("respuesta", ""))
            ok_datos, detalle = comparar(valores, str(p.valores_esperados).split(";"),
                                         str(p.tolerancias).split(";"), str(p.unidades).split(";"))
            interp, nota_interp = "", ""
            if p.tipo == "mixta":
                if (modo, pid) in rev.index:
                    interp = bool(rev.loc[(modo, pid), "cumple"])
                    nota_interp = rev.loc[(modo, pid), "nota"]
                else:
                    interp, nota_interp = False, "pendiente de revisión"
            correcto = ok_datos and (interp if p.tipo == "mixta" else True)
            sin_resp = valores is None or all("no disponible" in _norm(x) for x in valores.split(";"))
            estado = ("error" if r.get("error") else "sin respuesta" if sin_resp else
                      "correcta" if correcto else "incorrecta")
            herr = r.get("herramientas", [])
            consultas = [h for h in herr if h not in ("ToolSearch", "Glob")]
            respaldo = "solo memoria (sin consultar fuentes)" if not consultas else "herramientas"
            filas.append({
                "id": pid, "tipo": p.tipo, "modo": modo, "pregunta": p.pregunta,
                "respuesta_esperada": p.respuesta_esperada, "respuesta_generada": valores or "",
                "fuente_utilizada": fuentes_citadas(r.get("respuesta", ""), jsonl),
                "herramientas_usadas": ", ".join(f"{h}×{herr.count(h)}" for h in sorted(set(herr))) or "ninguna",
                "skills_usadas": ", ".join(sorted(set(r.get("skills", [])))) or "ninguna",
                "respaldo": respaldo,
                "correcto_datos": ok_datos, "interpretacion_ok": interp, "correcto": correcto, "estado": estado,
                "detalle": detalle, "nota_interpretacion": nota_interp,
                "tiempo_s": r.get("segundos"), "turnos": r.get("turnos"), "costo_usd": r.get("costo_usd"),
                "error": r.get("error", ""),
                "transcripcion": str(jsonl.with_suffix(".md").relative_to(RAIZ))})
    res = pd.DataFrame(filas)
    res.to_csv(AQUI / "resultados.csv", index=False, float_format="%.4f")
    cfg = {"modelo": MODELO, "herramientas_generales_ambos_modos": HERRAMIENTAS_GENERALES,
           "solo_modo_B": HERRAMIENTAS_B + ["MCP bcrp (.mcp.json)", "Skills de .claude/skills"],
           "instrucciones": INSTRUCCIONES}
    (AQUI / "configuracion_experimento.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    resumen = res.groupby("modo").agg(correctas=("correcto", "sum"), n=("correcto", "size"),
                                      sin_respuesta=("estado", lambda s: (s == "sin respuesta").sum()),
                                      errores=("estado", lambda s: (s == "error").sum()),
                                      tiempo_promedio_s=("tiempo_s", "mean"), tiempo_mediano_s=("tiempo_s", "median"),
                                      costo_total_usd=("costo_usd", "sum"),
                                      solo_memoria=("respaldo", lambda s: s.str.startswith("solo").sum()))
    por_tipo = res.pivot_table(index="tipo", columns="modo", values="correcto", aggfunc="sum")
    print(resumen.to_string())
    print(por_tipo.to_string())
    print(res[["id", "modo", "estado", "respuesta_generada", "tiempo_s"]].to_string(index=False))
    return res, resumen, por_tipo


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "calificar"
    if accion == "correr":                       # correr, correr A o correr B
        correr_todo(tuple(sys.argv[2:]) or ("A", "B"))
    calificar()
