# Evidencias del uso de inteligencia artificial

Todo el proyecto se hizo con **Claude Code (Opus 5.5, `claude-opus-5-5`)**. Las conversaciones se entregan
exportadas (opción B de la consigna), en orden cronológico.

**Qué se ocultó:** el correo, las rutas personales (`/Users/...` aparece como `~`), las carpetas temporales, los
avisos internos del sistema y de la memoria del asistente, la lista de skills personales de la cuenta y los
resultados de comandos que mostraban información personal ajena a la tarea (por ejemplo, nombres de otros proyectos).
Cada omisión queda marcada en el texto. Los razonamientos internos del modelo no se guardan en el registro. No hay
claves API ni tokens: Claude Code usa la sesión iniciada de la cuenta y el BCRP no pide clave.

## 1. Desarrollo (conversación con la estudiante)

| Archivo | Qué cubre |
|---|---|
| [`desarrollo/tarea4_conversacion_completa.md`](desarrollo/tarea4_conversacion_completa.md) | La conversación del 8 de noviembre de 2026 en la que se hizo la Tarea 4: resumen de la consigna, servidor MCP y sus pruebas, las tres Skills y su validación, demostraciones, ejecución integrada, evaluación, correcciones, verificación y documentación |
| [`desarrollo/sesion04_desarrollo_servidor_mcp.md`](desarrollo/sesion04_desarrollo_servidor_mcp.md) | La conversación del 28-29 de octubre de 2026 en la que se desarrolló el servidor MCP de la Sesión 04 (`buscar_series`, `serie`, `resumen`, recurso, prompt, primeras herramientas propias y 8 pruebas), que es la base de `mcp/server.py` |

## 2. Sesiones del agente (`claude -p`)

Cada sesión está en dos formatos: `.md` (legible: herramientas disponibles, pedido, cada llamada con su resultado
y cierre con tiempo y costo) y `.jsonl` (el registro original de Claude Code, saneado).

| Carpeta | Sesiones |
|---|---|
| [`mcp/`](mcp/) | `demo_prompt_mcp_interpretar_indicador`: el prompt MCP `/mcp__bcrp__interpretar_indicador` · `demo_recurso_mcp_ficha_serie`: los recursos `bcrp://serie/{codigo}` y `bcrp://series-clave` con `resumen` |
| [`skills/`](skills/) | `demo1_mapa_encadena_skills`: «Haz un mapa…» activa `mapeando-enaho`, que pide antes `limpiando-enaho` · `demo2_invocacion_directa_graficando`: `/graficando-enaho sexo` · `demo3_pregunta_natural_cusco`: una pregunta activa `limpiando-enaho` |
| [`integracion/`](integracion/) | `ejecucion_agente`: la ejecución integrada (5 herramientas MCP + 3 Skills) que escribió `informes/informe_final.md`; `resumen_ejecucion.json` |
| [`evaluacion/`](evaluacion/) | `modo_A/` y `modo_B/`: las 10 preguntas en cada modo · `robustez/`: las 4 sesiones de la prueba de robustez |

Las sesiones de `claude -p` se lanzaron con los scripts del repositorio (`agente/ejecutar_agente.py`,
`evaluacion/evaluar.py`, `evaluacion/robustez.py`), que usan `evaluacion/claude_headless.py` para correr Claude Code y
transcribir cada sesión.
