# Demo 3 · Una pregunta en lenguaje natural activa limpiando-enaho

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
¿Cuál fue la pobreza monetaria en Cusco en 2024 según la ENAHO?
```

## Sesión

**→ Herramienta `Skill`**

```json
{
 "skill": "limpiando-enaho",
 "args": "pobreza monetaria en Cusco 2024"
}
```

<details><summary>Resultado</summary>

```text
Launching skill: limpiando-enaho
```

</details>

**→ Herramienta `Bash`**

```json
{
 "command": "ls -la datos/ salidas/ 2>&1",
 "description": "List data and output directories"
}
```

<details><summary>Resultado</summary>

```text
datos/:
total 42728
drwxr-xr-x@  6 melinarozas  staff       192 Nov  8 12:14 .
drwxr-xr-x@ 17 melinarozas  staff       544 Nov  8 12:11 ..
-rw-r--r--@  1 melinarozas  staff   5793097 Nov  8 12:05 966-Modulo02.zip
-rw-r--r--@  1 melinarozas  staff  15935617 Nov  8 12:05 966-Modulo34.zip
drwxr-xr-x@  3 melinarozas  staff        96 Nov  8 12:14 bcrp
-rw-r--r--@  1 melinarozas  staff    139681 Nov  8 12:05 peru_departamental_simple.geojson

salidas/:
total 2696
drwxr-xr-x@ 15 melinarozas  staff      480 Nov  8 12:19 .
drwxr-xr-x@ 17 melinarozas  staff      544 Nov  8 12:11 ..
-rw-r--r--@  1 melinarozas  staff     2096 Nov  8 12:19 comparacion_mapa_referencia.csv
-rw-r--r--@  1 melinarozas  staff      236 Nov  8 12:14 figura_area.csv
-rw-r--r--@  1 melinarozas  staff     2017 Nov  8 12:14 figura_departamento.csv
-rw-r--r--@  1 melinarozas  staff      786 Nov  8 12:14 figura_dominio.csv
-rw-r--r--@  1 melinarozas  staff      453 Nov  8 12:14 figura_edad.csv
-rw-r--r--@  1 melinarozas  staff      309 Nov  8 12:14 figura_region.csv
-rw-r--r--@  1 melinarozas  staff      207 Nov  8 12:14 figura_sexo.csv
-rw-r--r--@  1 melinarozas  staff      257 Nov  8 12:14 figura_sexo_jefe.csv
-rw-r--r--@  1 melinarozas  staff     9074 Nov  8 12:19 indicadores.csv
-rw-r--r--@  1 melinarozas  staff  1318454 Nov  8 12:19 personas_2024.parquet
-rw-r--r--@  1 melinarozas  staff     1299 Nov  8 12:09 pruebas_mcp.txt
-rw-r--r--@  1 melinarozas  staff     5242 Nov  8 12:19 validacion.txt
-rw-r--r--@  1 melinarozas  staff     1068 Nov  8 12:19 validacion_mapa.txt
```

</details>

**Claude:**

The skill says to run the script as-is; the zips are already present.

**→ Herramienta `Bash`**

```json
{
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/limpiando-enaho/scripts/limpiar.py; echo \"EXIT=$?\"",
 "description": "Run ENAHO cleaning and validation script",
 "timeout": 300000
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
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/limpiando-enaho/scripts/limpiar.py",
 "description": "Run ENAHO cleaning and validation script",
 "timeout": 300000
}
```

<details><summary>Resultado</summary>

```text
Leídos 966-Modulo34/sumaria-2024.dta: 33,691 hogares y 966-Modulo02/enaho01-2024-200.dta: 117,721 personas
VALIDACIÓN ENAHO 2024 · generado 2026-11-08 12:20
Archivos: 966-Modulo34.zip/966-Modulo34/sumaria-2024.dta y 966-Modulo02.zip/966-Modulo02/enaho01-2024-200.dta
Filtro de residentes: ((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))
Unión: personas.merge(sumaria, on=[conglome, vivienda, hogar], validate='m:1')
Pobreza: pobre = pobreza <= 2; ponderación con facpob07 (personas). Error estándar por diseño (conglome dentro de estrato).

[OK] Llaves de sumaria como texto con ceros iniciales (conglome, vivienda, hogar)             valor: sí                     referencia: sí                         APROBADA (esencial)
[OK] Llaves únicas en sumaria                                                                 valor: 0 duplicados           referencia: 0 duplicados               APROBADA (esencial)
[OK] Llaves de miembros como texto con ceros iniciales (conglome, vivienda, hogar, codperso)  valor: sí                     referencia: sí                         APROBADA (esencial)
[OK] Llaves únicas en miembros                                                                valor: 0 duplicados           referencia: 0 duplicados               APROBADA (esencial)
[OK] Hogares en la sumaria                                                                    valor: 33,691                 referencia: 33,691                     APROBADA (esencial)
[OK] Residentes habituales                                                                    valor: 108,664                referencia: 108,664                    APROBADA (esencial)  · de 117,721 filas del módulo 02
[OK] Unión m:1 sin duplicar filas                                                             valor: 108,664 -> 108,664     referencia: igual número de filas      APROBADA (esencial)
[OK] Todas las personas encuentran su hogar                                                   valor: 0 sin hogar            referencia: 0                          APROBADA (esencial)
[OK] Persona única después de la unión                                                        valor: 0 duplicados           referencia: 0                          APROBADA (esencial)
[OK] El ubigeo de la persona coincide con el del hogar                                        valor: 100.00%                referencia: 100 %                      APROBADA (informativa)
[OK] Códigos de departamento (ubigeo[:2])                                                     valor: 25: 01-25              referencia: 25: 01-25                  APROBADA (esencial)
[OK] Lima (15) y Callao (07) separados                                                        valor: sí                     referencia: sí                         APROBADA (esencial)
[OK] facpob07 presente y positivo en todos los residentes                                     valor: 0 nulos o <= 0         referencia: 0                          APROBADA (esencial)
[OK] Población expandida (suma de
… [recortado: 2290 caracteres más]
```

</details>

**→ Herramienta `Grep`**

```json
{
 "pattern": "(?i)cusco|^corte|^indicador|^nivel|^grupo|^tipo",
 "path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/indicadores.csv",
 "output_mode": "content"
}
```

<details><summary>Resultado</summary>

```text
32:2024,departamento,08,Cusco,18.5393,2.0120,14.5958,22.4828,10.8500,3777,1380357,18.5413,pobreza_monetaria,"INEI, ENAHO 2024 (módulos 34 y 02); cálculo propio ponderado con facpob07"
```

</details>

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/indicadores.csv",
 "limit": 2
}
```

<details><summary>Resultado</summary>

```text
1	anio,dimension,codigo,categoria,pobreza_pct,ee,ic_inf,ic_sup,cv_pct,n_muestra,poblacion_expandida,pobreza_pct_metodo_inei,indicador,fuente
2	2024,nacional,PE,Perú,27.5287,0.5194,26.5107,28.5467,1.8900,108664,34147766,27.5795,pobreza_monetaria,"INEI, ENAHO 2024 (módulos 34 y 02); cálculo propio ponderado con facpob07"
```

</details>

**Claude:**

Según la ENAHO 2024, el **18.5 %** de la población de Cusco era pobre monetariamente (IC 95 %: 14.6 %–22.5 %). Eso equivale a unas 255 mil de las 1,380,357 personas que tiene el departamento según la expansión de la encuesta (INEI, ENAHO 2024).

| | Pobreza monetaria | IC 95 % | Muestra |
|---|---|---|---|
| **Cusco** | **18.5 %** | 14.6–22.5 | 3,777 personas |
| Perú | 27.5 % | 26.5–28.5 | 108,664 personas |

- **Comparación con el país:** Cusco está claramente por debajo del promedio nacional. Los dos intervalos no se superponen, así que la diferencia no se explica por el error de muestreo.
- **Precisión:** el error estándar es 2.0 puntos y el coeficiente de variación es 10.9 %. Como la muestra departamental es más chica que la nacional, el intervalo es más ancho (unos ±4 puntos). Conviene citar el intervalo junto con el 18.5 %.
- **Método:** la cifra se calcula sobre los residentes habituales, ponderando con `facpob07`, y el error estándar sigue el diseño muestral. Con el método oficial del INEI (sumaria, `factor07 × mieperho`) da prácticamente lo mismo: 18.54 %.

**De dónde sale:** volví a correr `limpiar.py` y pasó las 22 verificaciones; a nivel nacional reproduce la cifra oficial (27.53 % frente a 27.6 %). El dato de Cusco está en `salidas/indicadores.csv`, en la fila `departamento, 08, Cusco`.

Al correr el script se reescribieron los archivos de `salidas/`, entre ellos `validacion.txt`, que ya tenía cambios sin commitear.

## Cierre

- Estado: success · turnos: 8 · duración: 30.8 s · costo estimado: US$ 0.19

