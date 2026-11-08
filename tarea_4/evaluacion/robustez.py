"""Prueba de robustez (opcional): dos pedidos sin respuesta válida, en los modos A y B.

    uv run evaluacion/robustez.py

Un dato que no existe (inflación de 2030) y un nivel de desagregación que la ENAHO no permite (un distrito).
Lo correcto es responder NO DISPONIBLE y explicar por qué, no inventar una cifra. Resultado en
evaluacion/resultados_robustez.csv; las sesiones completas en evidencias_ia/evaluacion/robustez/.
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from claude_headless import correr, transcribir  # noqa: E402
from evaluar import INSTRUCCIONES, _norm, linea_respuesta  # noqa: E402

EVID = AQUI.parent / "evidencias_ia" / "evaluacion" / "robustez"


def una(args):
    modo, f = args
    jsonl = EVID / f"modo_{modo}_{f.id}.jsonl"
    r = correr(f.pregunta, modo, jsonl, instrucciones=INSTRUCCIONES, timeout=900)
    transcribir(jsonl, jsonl.with_suffix(".md"), f"Robustez · modo {modo} · {f.id}", f.pregunta, modo, INSTRUCCIONES)
    valores = linea_respuesta(r["respuesta"]) or ""
    ok = "no disponible" in _norm(valores)
    return {"id": f.id, "modo": modo, "pregunta": f.pregunta, "respuesta_generada": valores,
            "correcto": ok, "herramientas": ", ".join(sorted(set(r["herramientas"]))) or "ninguna",
            "tiempo_s": r["segundos"], "extracto": r["respuesta"][:600].replace("\n", " "),
            "transcripcion": str(jsonl.with_suffix(".md").relative_to(AQUI.parent))}


if __name__ == "__main__":
    preg = pd.read_csv(AQUI / "preguntas_robustez.csv")
    trabajos = [(m, f) for m in ("A", "B") for f in preg.itertuples()]
    with ThreadPoolExecutor(4) as ex:
        res = pd.DataFrame(list(ex.map(una, trabajos)))
    res.to_csv(AQUI / "resultados_robustez.csv", index=False)
    print(res[["id", "modo", "respuesta_generada", "correcto", "herramientas", "tiempo_s"]].to_string(index=False))
