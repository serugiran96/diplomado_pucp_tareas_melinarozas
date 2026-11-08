# Robustez · modo B · R2_distrito_enaho

- **Modo:** B · **Modelo:** claude-opus-5-5 · **Claude Code:** 2.1.319
- **Carpeta:** `~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4`
- **Servidores MCP:** bcrp (connected)
- **Herramientas MCP:** mcp__bcrp__buscar_series, mcp__bcrp__comparar_paises, mcp__bcrp__comparar_periodos, mcp__bcrp__correlacion, mcp__bcrp__graficar_serie, mcp__bcrp__resumen, mcp__bcrp__serie
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho (otras 0 skills generales de Claude Code o de la cuenta, no relacionadas con el proyecto, se omiten aquí)
- **Permisos:** acceptEdits

**Instrucciones añadidas al sistema (iguales en ambos modos):**

> Responde en español. Da la cifra pedida con su unidad, el periodo y la fuente que usaste. No inventes datos: si no puedes obtener o verificar una cifra, dilo. Termina siempre con una última línea con el formato `RESPUESTA: valor1; valor2; ...` con los valores pedidos en el orden de la pregunta (números con punto decimal y sin el signo %, meses como AAAA-MM, respuestas de sí o no como sí o no). Si no tienes un valor, escribe NO DISPONIBLE en su lugar.

## Pedido

```text
Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria del distrito de Miraflores, en Lima, en %?
```

## Sesión

**→ Herramienta `Glob`**

```json
{
 "pattern": "**/*.{parquet,csv,dta,sav}"
}
```

<details><summary>Resultado</summary>

```text
.venv/lib/python3.14/site-packages/pyogrio/tests/fixtures/list_nested_struct_file.parquet
.venv/lib/python3.14/site-packages/pyogrio/tests/fixtures/list_field_values_file.parquet
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_5.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_10_191.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_10.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_7.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/gt_datum.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_3.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_2.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_5.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_6.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_4.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_6.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_4.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_0.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_1.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_5.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_7.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_3.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_1.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_20_1.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_5.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_4.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_20_0.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_0.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_2_0.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_2.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_20_2.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_6.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_4_7.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_20_3.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_3.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_17.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_3_6.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_16.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_0_14.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_table_4_2_3_5.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/s57attributes.csv
.venv/lib/python3.14/site-packages/pyogrio/gdal_data/grib2_
… [recortado: 5036 caracteres más]
```

</details>

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/limpiando-enaho/SKILL.md"
}
```

<details><summary>Resultado</summary>

```text
1	---
2	name: limpiando-enaho
3	description: Limpia y une los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, filtra residentes habituales, aplica el factor de expansión y valida la pobreza monetaria contra la cifra oficial (27.6 %). Úsala cuando pidan limpiar, preparar, unir o validar la ENAHO, o calcular pobreza monetaria o extrema del Perú en 2024 por departamento, área urbana o rural, sexo, edad, región o dominio. Las skills graficando-enaho y mapeando-enaho la necesitan antes.
4	argument-hint: "[--descargar]"
5	---
6	
7	# Limpiar la ENAHO 2024
8	
9	Lo que no se discute (lectura, llaves, filtro, unión, factores, validación) está en `scripts/limpiar.py`.
10	No lo reescribas ni lo reemplaces con código improvisado: córrelo tal cual.
11	
12	## Pasos
13	
14	1. Revisa si existen `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` (966 = ENAHO 2024 en el portal del INEI).
15	2. Corre exactamente, desde la raíz del proyecto:
16	
17	   ```bash
18	   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py            # si los zip ya están en datos/
19	   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --descargar  # si faltan: los baja del INEI
20	   ```
21	
22	3. Lee `salidas/validacion.txt`. Si dice `RESULTADO: FALLÓ` o el script terminó con código 1, **detente**:
23	   informa qué verificación esencial falló y no calcules nada más. Nunca ajustes cifras para que coincidan.
24	4. Si aprobó, responde con lo que generó el script:
25	   - `salidas/indicadores.csv`: pobreza ponderada por nacional, área, sexo, sexo del jefe de hogar, grupo de
26	     edad, región natural, dominio y departamento, con error estándar, IC 95 % y tamaño de muestra.
27	   - `salidas/personas_2024.parquet`: la base de 108,664 residentes, para cortes que no estén en la tabla.
28	5. Para un corte nuevo usa la función ponderada del script, nunca `mean()` simple:
29	
30	   ```bash
31	   uv run python -c "
32	   import sys, pandas as pd; sys.path.insert(0, '${CLAUDE_SKILL_DIR}/scripts')
33	   from estimacion import proporcion
34	   b = pd.read_parquet('salidas/personas_2024.parquet')
35	   print(proporcion(b, 'pobre', dominio=(b.area == 'Rural') & (b.sexo == 'Mujer')))"
36	   ```
37	
38	6. Al citar una cifra di: el valor con un decimal, el IC 95 %, «INEI, ENAHO 2024» y el archivo de donde sale.
39	   Una diferencia entre grupos cuyos IC se superponen no es una diferencia clara: dilo así.
40	7. Antes de usar una variable que no está en la base, o si piden explicar el método, lee
41	   [reference.md](reference.md).
42	
43	## Qué no hacer
44	
45	- No uses promedios simples: toda proporción va ponderada con `facpob07`.
46	- No presentes asociaciones como causas.
47	- No escribas cifras de memoria: si el script o la tabla no la tienen, dilo.
48	
```

</details>

**→ Herramienta `Bash`**

```json
{
 "command": "ls salidas datos 2>&1; grep -n -i -E \"distrit|ubigeo|inferencia|representativ\" .claude/skills/limpiando-enaho/reference.md",
 "description": "List outputs and search reference for district notes"
}
```

<details><summary>Resultado</summary>

```text
datos:
966-Modulo02.zip
966-Modulo34.zip
bcrp
peru_departamental_simple.geojson

salidas:
comparacion_mapa_referencia.csv
figura_area.csv
figura_departamento.csv
figura_dominio.csv
figura_edad.csv
figura_region.csv
figura_sexo.csv
figura_sexo_jefe.csv
indicadores.csv
personas_2024.parquet
pruebas_mcp.txt
validacion.txt
validacion_mapa.txt
16:   (`conglome` 6, `vivienda` 3, `hogar` 2, `codperso` 2, `ubigeo` 6) para no perder ceros iniciales.
27:| `departamento` | `ubigeo[:2]` (texto, 01-25; Lima 15 y Callao 07 separados) |
```

</details>

**→ Herramienta `Bash`**

```json
{
 "command": "tail -5 salidas/validacion.txt; uv run python -c \"\nimport sys, pandas as pd; sys.path.insert(0, '.claude/skills/limpiando-enaho/scripts')\nfrom estimacion import proporcion\nb = pd.read_parquet('salidas/personas_2024.parquet')\nprint(b.columns.tolist())\nm = b.ubigeo.astype(str).str.zfill(6) == '150122'\nprint('personas', m.sum(), 'hogares', b.loc[m, ['conglome','vivienda','hogar']].drop_duplicates().shape[0], 'conglomerados', b.loc[m,'conglome'].nunique())\nprint(proporcion(b, 'pobre', dominio=m))\n\"",
 "description": "Check Miraflores sample in ENAHO 2024 microdata"
}
```

<details><summary>Resultado</summary>

```text
[OK] Pobreza en Lima Metropolitana (dominio 8)                                                valor: 28.03 % | 28.21 %      referencia: ≈ 28.2 %                   APROBADA (informativa)  · personas+facpob07 | sumaria+factor07×mieperho; dif. entre métodos -0.18 pp
[OK] Departamentos con estimación en indicadores.csv                                          valor: 25                     referencia: 25                         APROBADA (esencial)

Resumen: 22/22 verificaciones aprobadas; 0 esenciales fallidas.
RESULTADO: APROBADA. Base guardada en salidas/personas_2024.parquet (108,664 personas) e indicadores en salidas/indicadores.csv.
['conglome', 'vivienda', 'hogar', 'codperso', 'ubigeo', 'departamento', 'departamento_nombre', 'dominio', 'dominio_nombre', 'region_natural', 'estrato', 'area', 'p203', 'sexo', 'sexo_jefe', 'edad', 'grupo_edad', 'pobreza', 'pobre', 'pobre_extremo', 'facpob07', 'factor07', 'mieperho', 'linea', 'gashog2d', 'inghog2d', 'anio']
personas 131 hogares 61 conglomerados 11
{'pct': np.float64(0.0), 'ee': 0.0, 'ic_inf': np.float64(0.0), 'ic_sup': np.float64(0.0), 'cv_pct': None, 'n': 131, 'poblacion': 78454}
```

</details>

**Claude:**

La ENAHO 2024 no da una tasa de pobreza válida para el distrito de Miraflores. La encuesta está diseñada para dar cifras del país, del área urbana y rural, de los dominios y de los departamentos, no de los distritos.

Busqué el ubigeo 150122 en los microdatos ya validados (`salidas/personas_2024.parquet`; `salidas/validacion.txt` aprobó 22 de 22 controles) y calculé la tasa ponderada con `facpob07`:

| Dato | Valor |
|---|---|
| Personas en la muestra | 131 |
| Hogares | 61 |
| Conglomerados | 11 |
| Personas pobres en la muestra | 0 |
| Resultado directo | 0.0 % (error estándar 0, IC 95 % 0.0–0.0) |

Ese 0.0 % no es la tasa del distrito. Solo significa que ninguno de los 61 hogares de la muestra quedó bajo la línea de pobreza. El error estándar de cero no indica precisión: con cero casos pobres la fórmula no puede medir la incertidumbre, y 11 conglomerados son muy pocos para estimar un distrito. Por eso no lo doy como respuesta.

Hay dos alternativas:
- **Lima Metropolitana (dominio 8)**, el nivel más cercano que la ENAHO 2024 sí representa: 28.0 % de pobreza monetaria en 2024 (INEI, ENAHO 2024; `salidas/validacion.txt`).
- **La cifra por distrito** sale del *Mapa de pobreza monetaria provincial y distrital* del INEI. Su última edición es de 2018 y combina el Censo 2017 con la ENAHO. No la consulté en esta sesión, así que no te doy el valor de memoria. Si quieres, la busco.

RESPUESTA: NO DISPONIBLE

## Cierre

- Estado: success · turnos: 5 · duración: 24.1 s · costo estimado: US$ 0.20

