# Verificación de cifras del informe final

Seis afirmaciones numéricas de [`informe_final.md`](informe_final.md), tres del BCRP y tres de la ENAHO, comprobadas
por un camino distinto del que usó el agente:

- **Recálculo independiente** con [`verificar_cifras.py`](verificar_cifras.py): pide las series directamente a la
  API del BCRP (sin el servidor MCP) y recalcula la ENAHO con la sumaria y `factor07 × mieperho` (sin las Skills).
  Resultado en [`verificacion_cifras.csv`](verificacion_cifras.csv).
- **Revisión manual en la fuente oficial**: el enlace de cada fila abre la tabla del BCRP o la publicación del INEI
  donde se lee la cifra. La última columna la marca la estudiante al revisar la fuente por sí misma.

| # | Afirmación del informe | Valor del informe | Valor recalculado | Fuente para revisar a mano | ¿Coincide? | Diferencia y explicación | Revisado a mano |
|---|---|---|---|---|---|---|---|
| 1 | La inflación anual (dic/dic) de Lima fue **1.97 %** en 2024 (Hallazgo 1) | 1.97 % | 1.9663 % | BCRP, serie PM05197PA: [tabla](https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/PM05197PA/html/2020/2024/) (muestra «2,0» redondeado) · [API](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PM05197PA/json/2024/2024) | Sí | 0.004 pp, por redondeo a dos decimales | ☐ |
| 2 | La inflación a 12 meses llegó a su máximo de **8.81 % en junio de 2022** (Hallazgo 1) | 8.81 %, 2022-06 | 8.8126 %, Jun.2022 | BCRP, serie PN01273PM: [tabla 2020-2024](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN01273PM/html/2020-1/2024-12/) · [API](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2020-1/2024-12) | Sí | 0.003 pp, por redondeo | ☐ |
| 3 | El PBI real creció **3.52 %** en 2024 (Hallazgo 3) | 3.52 % | 3.5153 % | BCRP, serie PM04923AA: [tabla](https://estadisticas.bcrp.gob.pe/estadisticas/series/anuales/resultados/PM04923AA/html/2020/2024/) · [API](https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PM04923AA/json/2024/2024) | Sí | 0.005 pp, por redondeo. Ojo: la primera estimación del BCRP (2025) fue 3.3 %; la serie actual, revisada, dice 3.52 % | ☐ |
| 4 | La pobreza monetaria nacional fue **27.5 %** en 2024 (Hallazgo 4) | 27.53 % | 27.58 % (método INEI) | INEI, *Evolución de la pobreza monetaria 2015-2024* (mayo de 2025): 27.6 %, según [Canal N](https://canaln.pe/actualidad/pobreza-monetaria-bajo-276-2024-segun-inei-n483303) y [Expreso](https://www.expreso.com.pe/economia/pobreza-cae-a-27-6-en-2024-segun-inei-gasto-per-capita-sigue-por-debajo-de-nivel-prepandemia-instituto-nacional-de-estadistica-e-informatica-noticia/1189129/) · `salidas/validacion.txt` | Sí (±0.1 pp) | −0.05 pp frente al recálculo y −0.07 pp frente al 27.6 % oficial: el informe cuenta a los residentes habituales del módulo 02 y el INEI usa `mieperho` ([reference.md](../.claude/skills/limpiando-enaho/reference.md)) | ☐ |
| 5 | La pobreza rural (**39.4 %**) superaba a la urbana (**24.7 %**) en **14.7 puntos** (Hallazgo 4) | 14.7 pp | 14.49 pp (39.30 − 24.81) | INEI: rural 39.3 % y urbana 24.8 %, según [Forbes Perú](https://forbes.pe/economia-y-finanzas/2025-05-09/pobreza-monetaria-se-redujo-en-2024-esto-es-lo-que-hay-que-saber/) · `salidas/indicadores.csv` | Sí, con diferencia explicada | +0.21 pp en la brecha (+0.14 rural, −0.07 urbana), por la misma diferencia de población contada. Las cifras oficiales caen dentro del IC 95 % del informe (rural 37.8-41.1; urbana 23.5-25.9) | ☐ |
| 6 | Cajamarca fue el departamento más pobre, con **45.0 %** (Hallazgo 6) | 45.0 % | 45.01 % | INEI: Cajamarca 45.0 %, según [Bloomberg Línea](https://www.bloomberglinea.com/latinoamerica/peru/los-departamentos-mas-golpeados-por-la-pobreza-monetaria-en-peru-segun-el-inei/) · [referencia de la Sesión 16](../.claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv) | Sí | 0.01 pp | ☐ |

**Resultado:** 6/6 afirmaciones coinciden con el recálculo independiente dentro de la tolerancia definida (±0.005 pp
para series del BCRP, ±0.1 pp para tasas de la ENAHO y ±0.3 pp para una brecha, que suma el error de dos tasas).
Ninguna diferencia supera el redondeo o la diferencia documentada entre los dos métodos de ponderación de la ENAHO.

## Manejo de errores observado

Casos reales en los que una herramienta falló, no encontró datos o devolvió algo incompatible, y lo que hizo el
sistema en vez de inventar:

| Situación | Dónde se ve | Qué pasó |
|---|---|---|
| `buscar_series("pbi var% 12 meses")` devolvió 0 resultados | [ejecución integrada](../evidencias_ia/integracion/ejecucion_agente.md), Registro de herramientas del informe | El agente reformuló la búsqueda y lo dejó documentado. Después se agregaron sinónimos al buscador (`var% 12 meses` ↔ `variación porcentual interanual`) y ahora esa búsqueda encuentra PN01728AM primero |
| `resumen` devolvía una «variación %» de una tasa (p. ej. −976 %) | informe, Registro de herramientas; [demo del recurso MCP](../evidencias_ia/mcp/demo_recurso_mcp_ficha_serie.md) | El agente ignoró ese campo y usó el cambio en puntos porcentuales. Se corrigió el servidor: para series que ya son tasas, `variacion_pct` es `None` y se explica por qué |
| Una descarga directa con `curl` necesitaba un permiso que no tenía | informe, sección de contraste | El agente dijo que no la hizo y contrastó con otra serie del BCRP. La descarga independiente se hizo en este documento |
| Código de serie inexistente (`XX999`) | `mcp/test_server.py` (2 pruebas) | El servidor responde con un `ToolError` que nombra el código; nunca devuelve una cifra |
| Falta la base procesada de la ENAHO | [demo 1](../evidencias_ia/skills/demo1_mapa_encadena_skills.md) | `mapear.py` responde `FALTA LA BASE` (código 2) y Claude corre primero `limpiando-enaho` |
| Una validación esencial de la ENAHO falla | `limpiar.py` | El script escribe `RESULTADO: FALLÓ`, no guarda la base y termina con código 1; la skill indica detenerse |
