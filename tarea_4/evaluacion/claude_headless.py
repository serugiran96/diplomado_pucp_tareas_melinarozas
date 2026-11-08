"""Corre Claude Code sin interfaz (`claude -p`) en uno de dos modos y guarda la sesión completa.

    modo "A": sin el MCP del BCRP ni las Skills del proyecto. Corre en una carpeta vacía fuera del repositorio
              (no puede leer salidas/ ni indicadores ya calculados) con --strict-mcp-config sin servidores y
              --disallowedTools Skill.
    modo "B": con el MCP del BCRP (--mcp-config .mcp.json --strict-mcp-config) y las Skills de .claude/skills,
              en la carpeta del proyecto.

En los dos modos: el mismo modelo, las mismas instrucciones (--append-system-prompt) y las mismas herramientas
generales permitidas (Read, Glob, Grep, WebSearch, WebFetch, Bash con uv run / python3 / ls). Cada llamada es
una sesión nueva e independiente. Los hooks del usuario se desactivan solo para esa ejecución.

También convierte la salida stream-json en una transcripción Markdown legible, sin datos personales.
"""
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODELO = "claude-opus-5-5"
HERRAMIENTAS_GENERALES = ["Read", "Glob", "Grep", "WebSearch", "WebFetch", "Bash(uv run:*)", "Bash(python3:*)",
                          "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(wc:*)", "Bash(echo:*)", "Bash(test:*)"]
HERRAMIENTAS_B = ["mcp__bcrp__*", "Skill", "Write", "Edit"]
SKILLS_PROYECTO = {"limpiando-enaho", "graficando-enaho", "mapeando-enaho"}
CARPETA_A = Path(tempfile.gettempdir()) / "tarea4_modo_A_sin_herramientas"


def comando(prompt, modo, instrucciones=None, extra_permitidas=()):
    """La línea de comando de `claude -p` para un modo. Devuelve (args, cwd)."""
    args = ["claude", "-p", prompt, "--model", MODELO, "--output-format", "stream-json", "--verbose",
            "--settings", json.dumps({"disableAllHooks": True})]
    if instrucciones:
        args += ["--append-system-prompt", instrucciones]
    if modo == "A":
        CARPETA_A.mkdir(exist_ok=True)
        args += ["--strict-mcp-config", "--disallowedTools", "Skill",
                 "--allowedTools", *HERRAMIENTAS_GENERALES, *extra_permitidas]
        return args, CARPETA_A
    if modo == "B":
        args += ["--mcp-config", str(RAIZ / ".mcp.json"), "--strict-mcp-config", "--permission-mode", "acceptEdits",
                 "--allowedTools", *HERRAMIENTAS_GENERALES, *HERRAMIENTAS_B, *extra_permitidas]
        return args, RAIZ
    raise ValueError(f"modo desconocido: {modo}")


def correr(prompt, modo, salida_jsonl, instrucciones=None, timeout=900, extra_permitidas=()):
    """Ejecuta una sesión y devuelve un resumen: respuesta, herramientas usadas, tiempo, turnos y errores."""
    args, cwd = comando(prompt, modo, instrucciones, extra_permitidas)
    salida_jsonl = Path(salida_jsonl)
    salida_jsonl.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.time()
    error = ""
    try:
        with open(salida_jsonl, "w", encoding="utf-8") as f:
            proc = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
                                  timeout=timeout, text=True)
        if proc.returncode != 0:
            error = f"código de salida {proc.returncode}"
    except subprocess.TimeoutExpired:
        error = f"tiempo agotado ({timeout} s)"
    segundos = round(time.time() - inicio, 1)
    r = leer(salida_jsonl)
    sanear_jsonl(salida_jsonl)
    r.update({"modo": modo, "segundos": segundos, "error": error or r.get("error", "")})
    return r


def leer(ruta_jsonl):
    """Resume una sesión stream-json: texto final, herramientas y skills usadas, turnos, costo y errores."""
    herramientas, skills, eventos = [], [], []
    final = {}
    for linea in Path(ruta_jsonl).read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        eventos.append(d)
        if d.get("type") == "assistant":
            for b in d["message"].get("content", []):
                if b.get("type") == "tool_use":
                    herramientas.append(b["name"])
                    if b["name"] == "Skill":
                        skills.append(b["input"].get("skill") or b["input"].get("command") or "?")
        elif d.get("type") == "result":
            final = d
    return {"respuesta": final.get("result", ""), "herramientas": herramientas, "skills": skills,
            "turnos": final.get("num_turns"), "costo_usd": final.get("total_cost_usd"),
            "duracion_ms": final.get("duration_ms"),
            "error": "" if final and not final.get("is_error") else ("sin resultado" if not final else
                                                                       final.get("subtype", "error"))}


# ---------- transcripción ----------
PRIVADO = [(re.compile(re.escape(str(Path.home()))), "~"),
           (re.compile(r"[\w.+-]+@(?:gmail|hotmail|outlook|yahoo)\.com"), "[correo oculto]"),
           (re.compile(r"/private/var/folders/[^\s\"']+|/var/folders/[^\s\"']+"), "[carpeta temporal]")]


def limpiar_texto(s):
    s = str(s)
    for patron, reemplazo in PRIVADO:
        s = patron.sub(reemplazo, s)
    return s


def _recortar(s, n):
    s = limpiar_texto(s)
    return s if len(s) <= n else s[:n] + f"\n… [recortado: {len(s) - n} caracteres más]"


def transcribir(ruta_jsonl, ruta_md, titulo, prompt, modo, instrucciones=None):
    """Convierte stream-json a Markdown: herramientas disponibles, cada mensaje, cada llamada y su resultado."""
    lineas = [f"# {titulo}", ""]
    for linea in Path(ruta_jsonl).read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            if linea.strip():
                lineas += ["```text", _recortar(linea, 500), "```"]
            continue
        t = d.get("type")
        if t == "system" and d.get("subtype") == "init":
            mcp = ", ".join(f"{s['name']} ({s['status']})" for s in d.get("mcp_servers", [])) or "ninguno"
            herr = [h for h in d.get("tools", []) if h.startswith("mcp__")]
            skills = d.get("skills", [])
            del_proyecto = sorted(SKILLS_PROYECTO & set(skills))
            lineas += [f"- **Modo:** {modo} · **Modelo:** {d.get('model')} · **Claude Code:** "
                       f"{d.get('claude_code_version')}",
                       f"- **Carpeta:** `{limpiar_texto(d.get('cwd'))}`",
                       f"- **Servidores MCP:** {mcp}",
                       f"- **Herramientas MCP:** {', '.join(herr) or 'ninguna'}",
                       f"- **Skills del proyecto disponibles:** {', '.join(del_proyecto) or 'ninguna'}"
                       f" (otras {len(skills) - len(del_proyecto)} skills generales de Claude Code o de la cuenta, "
                       "no relacionadas con el proyecto, se omiten aquí)",
                       f"- **Permisos:** {d.get('permissionMode')}", ""]
            if instrucciones:
                lineas += ["**Instrucciones añadidas al sistema (iguales en ambos modos):**", "",
                           f"> {instrucciones}", ""]
            lineas += ["## Pedido", "", "```text", prompt, "```", ""]
            if prompt.lstrip().startswith("/"):
                lineas += [f"> El pedido empieza con `{prompt.split()[0]}`: es una invocación directa. Claude Code "
                           "carga esas instrucciones (la skill o el prompt MCP) antes de responder, por eso no "
                           "aparece como una llamada a la herramienta `Skill`.", ""]
            lineas += ["## Sesión", ""]
        elif t == "assistant":
            for b in d["message"].get("content", []):
                if b.get("type") == "text" and b["text"].strip():
                    lineas += ["**Claude:**", "", limpiar_texto(b["text"]), ""]
                elif b.get("type") == "tool_use":
                    entrada = json.dumps(b.get("input", {}), ensure_ascii=False, indent=1)
                    lineas += [f"**→ Herramienta `{b['name']}`**", "", "```json", _recortar(entrada, 2500), "```", ""]
        elif t == "user":
            contenido = d.get("message", {}).get("content", [])
            for b in contenido if isinstance(contenido, list) else []:
                if b.get("type") == "tool_result":
                    c = b.get("content")
                    if isinstance(c, list):
                        c = "\n".join(x.get("text", "[imagen]") if isinstance(x, dict) else str(x) for x in c)
                    marca = "⚠️ Resultado con error" if b.get("is_error") else "Resultado"
                    lineas += [f"<details><summary>{marca}</summary>", "", "```text", _recortar(c, 3000), "```",
                               "", "</details>", ""]
        elif t == "system" and d.get("subtype") == "permission_denied":
            lineas += [f"> ⚠️ Permiso denegado para `{d.get('tool_name')}`: {limpiar_texto(d.get('message', ''))}", ""]
        elif t == "result":
            lineas += ["## Cierre", "",
                       f"- Estado: {d.get('subtype')} · turnos: {d.get('num_turns')} · duración: "
                       f"{(d.get('duration_ms') or 0) / 1000:.1f} s · costo estimado: US$ {d.get('total_cost_usd') or 0:.2f}",
                       ""]
    Path(ruta_md).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta_md).write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


CAMPOS_PRIVADOS_INIT = ("slash_commands", "terminal_slash_commands", "plugins", "agents", "memory_paths",
                        "messaging_socket_path", "apiKeySource", "capabilities", "uuid", "session_id")


def sanear_jsonl(ruta_jsonl):
    """Deja el JSONL listo para publicar: en el mensaje inicial solo quedan las skills del proyecto (no las de la
    cuenta) y se quitan comandos, plugins y rutas de memoria; se eliminan las firmas de razonamiento (no tienen
    contenido legible) y se ocultan la carpeta personal, correos y carpetas temporales."""
    ruta = Path(ruta_jsonl)
    salida = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue                                   # avisos de la terminal, no son parte de la sesión
        if d.get("type") == "system" and d.get("subtype") == "init":
            otras = [s for s in d.get("skills", []) if s not in SKILLS_PROYECTO]
            d["skills"] = sorted(SKILLS_PROYECTO & set(d.get("skills", [])))
            d["skills_omitidas"] = f"{len(otras)} skills generales de Claude Code o de la cuenta, no relacionadas"
            for campo in CAMPOS_PRIVADOS_INIT:
                d.pop(campo, None)
        if d.get("type") == "assistant":
            d["message"]["content"] = [b for b in d["message"].get("content", []) if b.get("type") != "thinking"]
            if not d["message"]["content"]:
                continue
        salida.append(limpiar_texto(json.dumps(_sin_imagenes(d), ensure_ascii=False)))
    ruta.write_text("\n".join(salida) + "\n", encoding="utf-8")
    return ruta


def _sin_imagenes(x):
    """Reemplaza las imágenes en base64 (figuras que el agente abrió para revisarlas) por una marca."""
    if isinstance(x, dict):
        if x.get("type") == "image" and isinstance(x.get("source"), dict):
            return {"type": "image", "source": {"type": "omitida", "nota": "imagen en base64 omitida; la figura "
                                                "está en figuras/ o mapas/"}}
        return {k: _sin_imagenes(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_sin_imagenes(v) for v in x]
    return x
