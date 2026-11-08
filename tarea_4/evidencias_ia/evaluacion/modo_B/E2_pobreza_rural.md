# Evaluación · modo B · E2_pobreza_rural

- **Modo:** B · **Modelo:** claude-opus-5-5 · **Claude Code:** 2.1.319
- **Carpeta:** `~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4`
- **Servidores MCP:** bcrp (connected)
- **Herramientas MCP:** mcp__bcrp__buscar_series, mcp__bcrp__comparar_paises, mcp__bcrp__comparar_periodos, mcp__bcrp__correlacion, mcp__bcrp__graficar_serie, mcp__bcrp__resumen, mcp__bcrp__serie
- **Skills del proyecto disponibles:** graficando-enaho, limpiando-enaho, mapeando-enaho (otras 33 skills generales de Claude Code o de la cuenta, no relacionadas con el proyecto, se omiten aquí)
- **Permisos:** acceptEdits

**Instrucciones añadidas al sistema (iguales en ambos modos):**

> Responde en español. Da la cifra pedida con su unidad, el periodo y la fuente que usaste. No inventes datos: si no puedes obtener o verificar una cifra, dilo. Termina siempre con una última línea con el formato `RESPUESTA: valor1; valor2; ...` con los valores pedidos en el orden de la pregunta (números con punto decimal y sin el signo %, meses como AAAA-MM, respuestas de sí o no como sí o no). Si no tienes un valor, escribe NO DISPONIBLE en su lugar.

## Pedido

```text
Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria en el área rural del Perú en 2024, en %?
```

## Sesión

**→ Herramienta `Grep`**

```json
{
 "pattern": "(?i)rural",
 "path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4",
 "output_mode": "content",
 "glob": "*.{txt,csv,md,json}",
 "head_limit": 60
}
```

<details><summary>Resultado</summary>

```text
agente/pregunta_investigacion.txt:1:Pregunta de investigación: ¿Cómo evolucionaron la inflación y la actividad económica del Perú entre 2020 y 2024, y qué brechas de pobreza monetaria entre departamentos y entre áreas urbana y rural había al cerrar ese período, según la ENAHO 2024?
agente/pregunta_investigacion.txt:7:3. ENAHO: usa las skills limpiando-enaho (revisa salidas/validacion.txt), graficando-enaho (área urbana y rural, y al menos otro grupo pertinente) y mapeando-enaho (mapa departamental).
.claude/skills/limpiando-enaho/SKILL.md:3:description: Limpia y une los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, filtra residentes habituales, aplica el factor de expansión y valida la pobreza monetaria contra la cifra oficial (27.6 %). Úsala cuando pidan limpiar, preparar, unir o validar la ENAHO, o calcular pobreza monetaria o extrema del Perú en 2024 por departamento, área urbana o rural, sexo, edad, región o dominio. Las skills graficando-enaho y mapeando-enaho la necesitan antes.
.claude/skills/limpiando-enaho/SKILL.md:35:   print(proporcion(b, 'pobre', dominio=(b.area == 'Rural') & (b.sexo == 'Mujer')))"
evaluacion/resultados.csv:7:E2_pobreza_rural,enaho,A,"Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria en el área rural del Perú en 2024, en %?",39.3 %,39.3,"INEI, ENAHO, búsqueda web, cdna.www.gob.pe, forbes.pe, www.gob.pe, www.infobae.com","ToolSearch×1, WebFetch×4, WebSearch×1",ninguna,True,,True,correcta,39.3 vs 39.3: ok,,45.7000,7,0.1325,,evidencias_ia/evaluacion/modo_A/E2_pobreza_rural.md
evaluacion/resultados.csv:11:[Omitted long matching line]
.claude/skills/limpiando-enaho/reference.md:28:| `area` | `Urbana` si `estrato <= 5`, `Rural` si `estrato >= 6` |
.claude/skills/limpiando-enaho/reference.md:56:difieren unas décimas (rural +0.14 pp, Lima Metropolitana −0.18 pp, Huánuco +0.5 pp). `indicadores.csv` trae
README.md:15:y qué brechas de pobreza monetaria entre departamentos y entre áreas urbana y rural había al cerrar ese período?
.claude/skills/graficando-enaho/SKILL.md:3:description: Genera gráficos de barras de la pobreza monetaria o extrema del Perú con la ENAHO 2024 del INEI, ponderados y con intervalos de confianza, por área urbana y rural, sexo, sexo del jefe de hogar, grupo de edad, región natural (costa, sierra, selva), dominio o departamento. Úsala cuando pidan graficar, visualizar o comparar en un gráfico la pobreza o las brechas de la ENAHO. Si no existe la base procesada, primero usa limpiando-enaho.
.claude/skills/graficando-enaho/SKILL.md:17:| urbano y rural, campo y ciudad, área de residencia | `area` |
salidas/figura_area.csv:3:pobre,área de residencia,Rural,39.4417,0.8477,37.7803,41.1031,2.1500,36071,6486385
evaluacion/preguntas.csv:7:E2_pobreza_rural,enaho,"Según la ENAHO 2024, ¿cuál fue la tasa de pobreza monetaria en el área rural del Perú en 2024, en %?",39.3,0.2,%,"39.3 %","INEI, ENAHO 2024 (sumaria, estrato >= 6); valor de validación de la Sesión 16",
evaluacion/preguntas.csv:11:
… [recortado: 9842 caracteres más]
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

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/validacion.txt"
}
```

<details><summary>Resultado</summary>

```text
1	VALIDACIÓN ENAHO 2024 · generado 2026-11-08 12:23
2	Archivos: 966-Modulo34.zip/966-Modulo34/sumaria-2024.dta y 966-Modulo02.zip/966-Modulo02/enaho01-2024-200.dta
3	Filtro de residentes: ((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))
4	Unión: personas.merge(sumaria, on=[conglome, vivienda, hogar], validate='m:1')
5	Pobreza: pobre = pobreza <= 2; ponderación con facpob07 (personas). Error estándar por diseño (conglome dentro de estrato).
6	
7	[OK] Llaves de sumaria como texto con ceros iniciales (conglome, vivienda, hogar)             valor: sí                     referencia: sí                         APROBADA (esencial)
8	[OK] Llaves únicas en sumaria                                                                 valor: 0 duplicados           referencia: 0 duplicados               APROBADA (esencial)
9	[OK] Llaves de miembros como texto con ceros iniciales (conglome, vivienda, hogar, codperso)  valor: sí                     referencia: sí                         APROBADA (esencial)
10	[OK] Llaves únicas en miembros                                                                valor: 0 duplicados           referencia: 0 duplicados               APROBADA (esencial)
11	[OK] Hogares en la sumaria                                                                    valor: 33,691                 referencia: 33,691                     APROBADA (esencial)
12	[OK] Residentes habituales                                                                    valor: 108,664                referencia: 108,664                    APROBADA (esencial)  · de 117,721 filas del módulo 02
13	[OK] Unión m:1 sin duplicar filas                                                             valor: 108,664 -> 108,664     referencia: igual número de filas      APROBADA (esencial)
14	[OK] Todas las personas encuentran su hogar                                                   valor: 0 sin hogar            referencia: 0                          APROBADA (esencial)
15	[OK] Persona única después de la unión                                                        valor: 0 duplicados           referencia: 0                          APROBADA (esencial)
16	[OK] El ubigeo de la persona coincide con el del hogar                                        valor: 100.00%                referencia: 100 %                      APROBADA (informativa)
17	[OK] Códigos de departamento (ubigeo[:2])                                                     valor: 25: 01-25              referencia: 25: 01-25                  APROBADA (esencial)
18	[OK] Lima (15) y Callao (07) separados                                                        valor: sí                     referencia: sí                         APROBADA (esencial)
19	[OK] facpob07 presente y positivo en todos los residentes                                     valor: 0 nulos o <= 0         referencia: 0                          APROBADA (esencial)
20	[OK] Población expandida (suma de facpob07)                                              
… [recortado: 2271 caracteres más]
```

</details>

**Claude:**

Según la ENAHO 2024 del INEI, la pobreza monetaria en el área rural del Perú fue de **39.3 %** en 2024. Es decir, alrededor de 4 de cada 10 personas del área rural eran pobres.

**De dónde sale la cifra**
- **Fuente:** INEI, ENAHO 2024, módulo 34 (sumaria) y módulo 02 (miembros del hogar). El área rural corresponde a los estratos 6 en adelante.
- **Periodo:** año 2024.
- **Cálculo:** lo hizo la skill `limpiando-enaho`. El archivo `salidas/validacion.txt`, generado hoy (2026-11-08 12:23), aprobó las 22 verificaciones.
  - **Método oficial del INEI** (sumaria, ponderada por factor07 × mieperho): **39.30 %**. Coincide con la cifra publicada por el INEI, de alrededor de 39.3 %.
  - **Método por personas** (ponderado con facpob07): **39.44 %**, con un intervalo de confianza al 95 % de 37.8 % a 41.1 % (n = 36,071 personas). Sale de `salidas/indicadores.csv`. Los dos métodos difieren en 0.14 puntos porcentuales.

Para contrastar, la pobreza urbana fue de 24.8 % y la nacional de 27.6 %, según el método oficial.

RESPUESTA: 39.3

## Cierre

- Estado: success · turnos: 4 · duración: 13.5 s · costo estimado: US$ 0.19

