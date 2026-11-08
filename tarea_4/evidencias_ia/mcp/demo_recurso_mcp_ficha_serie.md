# Demo MCP · Recursos bcrp://serie/{codigo} y bcrp://series-clave + herramienta resumen

```text
Warning: no stdin data received in 3s, proceeding without it. If piping from a slow command, redirect stdin explicitly: < /dev/null to skip, or wait longer.
```
- **Modo:** B · **Modelo:** claude-opus-5-5 · **Claude Code:** 2.1.319
- **Carpeta:** `~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4`
- **Servidores MCP:** bcrp (connected)
- **Herramientas MCP:** mcp__bcrp__buscar_series, mcp__bcrp__comparar_paises, mcp__bcrp__comparar_periodos, mcp__bcrp__correlacion, mcp__bcrp__graficar_serie, mcp__bcrp__resumen, mcp__bcrp__serie
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho (otras 33 skills generales de Claude Code o de la cuenta, no relacionadas con el proyecto, se omiten aquí)
- **Permisos:** acceptEdits

## Pedido

```text
Lee el recurso MCP bcrp://serie/PN01728AM y el recurso bcrp://series-clave del servidor bcrp. Dime qué mide la serie PN01728AM, su frecuencia y desde cuándo hay datos, y luego usa la herramienta resumen para darme su promedio en 2024, citando código, periodo y fuente.
```

## Sesión

**→ Herramienta `ToolSearch`**

```json
{
 "query": "select:ReadMcpResourceTool,mcp__bcrp__resumen",
 "max_results": 2
}
```

<details><summary>Resultado</summary>

```text
[imagen]
[imagen]
```

</details>

**→ Herramienta `ReadMcpResourceTool`**

```json
{
 "server": "bcrp",
 "uri": "bcrp://serie/PN01728AM"
}
```

<details><summary>Resultado</summary>

```text
{"contents":[{"uri":"bcrp://serie/PN01728AM","mimeType":"text/plain","text":"{\"codigo\": \"PN01728AM\", \"nombre\": \"Producto bruto interno y demanda interna (variaci\\u00f3n porcentual interanual) - PBI\", \"categoria\": \"PBI por sectores\", \"frecuencia\": \"Mensual\", \"inicio\": \"Ene-1995\", \"actualizada\": \"2026-10-23\"}"}]}
```

</details>

**→ Herramienta `ReadMcpResourceTool`**

```json
{
 "server": "bcrp",
 "uri": "bcrp://series-clave"
}
```

<details><summary>Resultado</summary>

```text
{"contents":[{"uri":"bcrp://series-clave","mimeType":"text/plain","text":"{\"series\": [{\"codigo\": \"PN01273PM\", \"descripcion\": \"Inflaci\\u00f3n de Lima Metropolitana, variaci\\u00f3n % del IPC en 12 meses (mensual)\"}, {\"codigo\": \"PN01271PM\", \"descripcion\": \"Inflaci\\u00f3n de Lima Metropolitana, variaci\\u00f3n % mensual del IPC (mensual)\"}, {\"codigo\": \"PM05197PA\", \"descripcion\": \"Inflaci\\u00f3n anual del IPC de Lima Metropolitana, variaci\\u00f3n % fin de periodo, dic/dic (anual)\"}, {\"codigo\": \"PM05217PA\", \"descripcion\": \"Inflaci\\u00f3n anual del IPC de Lima Metropolitana, variaci\\u00f3n % del \\u00edndice promedio (anual)\"}, {\"codigo\": \"PN09822PM\", \"descripcion\": \"Inflaci\\u00f3n de alimentos y bebidas en Lima Metropolitana, variaci\\u00f3n % en 12 meses (mensual)\"}, {\"codigo\": \"PN01728AM\", \"descripcion\": \"PBI real, variaci\\u00f3n % interanual (respecto al mismo mes del a\\u00f1o anterior) (mensual)\"}, {\"codigo\": \"PM04923AA\", \"descripcion\": \"PBI real, variaci\\u00f3n % anual (anual)\"}, {\"codigo\": \"PD04722MM\", \"descripcion\": \"Tasa de referencia de la pol\\u00edtica monetaria, % (mensual)\"}, {\"codigo\": \"PN01206PM\", \"descripcion\": \"Tipo de cambio interbancario venta, promedio del mes, S/ por US$ (mensual)\"}, {\"codigo\": \"PD04638PD\", \"descripcion\": \"Tipo de cambio interbancario venta, S/ por US$ (diaria)\"}], \"fuente\": \"https://estadisticas.bcrp.gob.pe/estadisticas/series/\"}"}]}
```

</details>

**→ Herramienta `mcp__bcrp__resumen`**

```json
{
 "codigo": "PN01728AM",
 "desde": "2024-1",
 "hasta": "2024-12"
}
```

<details><summary>Resultado</summary>

```text
{"codigo":"PN01728AM","nombre":"Producto bruto interno y demanda interna (variación porcentual interanual) - PBI","frecuencia":"Mensual","n":12,"primero":{"periodo":"2024-01","valor":1.831},"ultimo":{"periodo":"2024-12","valor":5.0662},"cambio":3.2352,"variacion_pct":176.6903,"promedio":3.4825,"maximo":{"periodo":"2024-05","valor":5.7069},"minimo":{"periodo":"2024-03","valor":-0.4097},"fuente":"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01728AM/json/2024-1/2024-12"}
```

</details>

**Claude:**

**Qué mide PN01728AM** (según `bcrp://serie/PN01728AM` y `bcrp://series-clave`):

- **Qué mide:** el crecimiento del PBI real de cada mes frente al mismo mes del año anterior (variación % interanual). El BCRP la registra como «Producto bruto interno y demanda interna (variación porcentual interanual) – PBI», en la categoría *PBI por sectores*.
- **Frecuencia:** mensual.
- **Datos desde:** enero de 1995. La última actualización es del 23 de octubre de 2026.
- En `series-clave` aparece junto a su versión anual, **PM04923AA** (PBI real, variación % anual).

**Promedio en 2024** (herramienta `resumen`):

| Dato | Valor |
|---|---|
| Código | PN01728AM |
| Periodo | 2024-01 a 2024-12 (12 meses) |
| **Promedio** | **3.48 %** |
| Máximo | 5.71 % (mayo 2024) |
| Mínimo | −0.41 % (marzo 2024) |
| Primer y último mes | 1.83 % (enero) → 5.07 % (diciembre) |

Fuente: BCRP, https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01728AM/json/2024-1/2024-12

Dos cosas a tener en cuenta:
- **El 3.48 % es el promedio de 12 tasas mensuales.** No es lo mismo que el crecimiento del PBI en todo 2024. Para la cifra anual oficial hay que consultar **PM04923AA**.
- **No uses la «variación %» de 176.7 % que devuelve la herramienta.** Como la serie ya es una tasa, ese número no tiene sentido económico. La comparación correcta es el **cambio**: el crecimiento interanual subió **3.24 puntos porcentuales** entre enero y diciembre.

## Cierre

- Estado: success · turnos: 5 · duración: 15.9 s · costo estimado: US$ 0.13

