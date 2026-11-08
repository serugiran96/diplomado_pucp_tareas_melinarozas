# Demo 2 · Invocación directa de una skill con /graficando-enaho

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
/graficando-enaho sexo
```

## Sesión

**→ Herramienta `Bash`**

```json
{
 "command": "ls salidas/ && uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/graficando-enaho/scripts/graficar.py --tipo sexo; echo \"EXIT=$?\"",
 "description": "Check processed data and run sex poverty chart script"
}
```

<details><summary>⚠️ Resultado con error</summary>

```text
This Bash command contains multiple operations. The following part requires approval: echo "EXIT=$?"
```

</details>

**→ Herramienta `Bash`**

```json
{
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/graficando-enaho/scripts/graficar.py --tipo sexo",
 "description": "Run poverty-by-sex chart script"
}
```

<details><summary>Resultado</summary>

```text
figuras/pobreza_sexo.png: La pobreza monetaria es similar en las mujeres (27.7 %) y los hombres (27.4 %): la diferencia está dentro del margen de error
categoria     pct  ic_inf  ic_sup     n
   Hombre 27.3706 26.2911 28.4502 52587
    Mujer 27.6757 26.6344 28.7170 56077
```

</details>

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/figuras/pobreza_sexo.png"
}
```

<details><summary>Resultado</summary>

```text
[imagen]
```

</details>

**Claude:**

Generé el gráfico y guardé la figura en `figuras/pobreza_sexo.png` y la tabla en `salidas/figura_sexo.csv`.

**Pobreza monetaria según sexo, Perú 2024 (% de personas, ponderado con `facpob07`)**

| Sexo | Pobreza | IC 95 % | n (muestra) |
|---|---|---|---|
| Hombre | 27.4 % | 26.3 – 28.5 | 52 587 |
| Mujer | 27.7 % | 26.6 – 28.7 | 56 077 |
| Promedio nacional | 27.5 % | | |

La pobreza es casi igual en mujeres y hombres. La diferencia es de unas 0.3 puntos porcentuales y los intervalos de confianza se superponen casi por completo. Está dentro del margen de error, así que no hay una brecha por sexo que se pueda afirmar con estos datos. Ambos grupos quedan muy cerca del promedio nacional.

Este resultado no significa que mujeres y hombres vivan la pobreza igual. La pobreza monetaria se mide por hogar: a todas las personas de un mismo hogar se les asigna la misma condición. Por eso este indicador casi no puede mostrar diferencias por sexo. Si te interesa una brecha de género, `--tipo sexo_jefe` (hogares con jefa mujer o jefe hombre) suele ser más informativo.

En la figura, el título se corta a la mitad de «(27.4 %)». Las cifras están bien, pero puedo ajustar dónde se parte la línea si vas a usar la imagen en la entrega.

## Cierre

- Estado: success · turnos: 4 · duración: 17.7 s · costo estimado: US$ 0.14

