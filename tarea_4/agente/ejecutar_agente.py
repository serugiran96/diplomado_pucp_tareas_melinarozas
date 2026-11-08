"""Ejecución integrada del agente (Parte 3): una sola sesión de Claude Code con el MCP del BCRP y las Skills.

    uv run agente/ejecutar_agente.py

Lee la pregunta y las instrucciones de agente/pregunta_investigacion.txt, corre `claude -p` en modo B y guarda
la sesión completa en evidencias_ia/integracion/ (JSONL original y transcripción Markdown). El informe lo
escribe el propio agente en informes/informe_final.md.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "evaluacion"))
from claude_headless import correr, transcribir  # noqa: E402

pedido = (RAIZ / "agente" / "pregunta_investigacion.txt").read_text(encoding="utf-8")
jsonl = RAIZ / "evidencias_ia" / "integracion" / "ejecucion_agente.jsonl"
r = correr(pedido, "B", jsonl, timeout=2400)
transcribir(jsonl, RAIZ / "evidencias_ia" / "integracion" / "ejecucion_agente.md",
            "Ejecución integrada del agente: MCP del BCRP + Skills de la ENAHO en una sola sesión", pedido, "B")
resumen = {k: v for k, v in r.items() if k != "respuesta"}
mcp = sorted({h for h in r["herramientas"] if h.startswith("mcp__")})
resumen.update({"herramientas_mcp_distintas": mcp, "skills_distintas": sorted(set(r["skills"]))})
(RAIZ / "evidencias_ia" / "integracion" / "resumen_ejecucion.json").write_text(
    json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(resumen, ensure_ascii=False, indent=1))
print(r["respuesta"])
ok = len(mcp) >= 2 and len(set(r["skills"])) >= 2
print(f"\nCondición de integración (>= 2 herramientas MCP y >= 2 skills en la misma ejecución): {'CUMPLE' if ok else 'NO CUMPLE'}")
