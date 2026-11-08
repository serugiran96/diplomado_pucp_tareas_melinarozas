# Evaluación · modo B · E3_pobreza_cusco

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
Según la ENAHO 2024, ¿cuál fue la pobreza monetaria del departamento de Cusco en 2024, en %?
```

## Sesión

**→ Herramienta `Skill`**

```json
{
 "skill": "limpiando-enaho",
 "args": "pobreza monetaria del departamento de Cusco 2024"
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
drwxr-xr-x@ 19 melinarozas  staff       608 Nov  8 12:26 ..
-rw-r--r--@  1 melinarozas  staff   5793097 Nov  8 12:05 966-Modulo02.zip
-rw-r--r--@  1 melinarozas  staff  15935617 Nov  8 12:05 966-Modulo34.zip
drwxr-xr-x@  3 melinarozas  staff        96 Nov  8 12:14 bcrp
-rw-r--r--@  1 melinarozas  staff    139681 Nov  8 12:05 peru_departamental_simple.geojson

salidas/:
total 2696
drwxr-xr-x@ 15 melinarozas  staff      480 Nov  8 12:19 .
drwxr-xr-x@ 19 melinarozas  staff      608 Nov  8 12:26 ..
-rw-r--r--@  1 melinarozas  staff     2096 Nov  8 12:24 comparacion_mapa_referencia.csv
-rw-r--r--@  1 melinarozas  staff      236 Nov  8 12:30 figura_area.csv
-rw-r--r--@  1 melinarozas  staff     2017 Nov  8 12:30 figura_departamento.csv
-rw-r--r--@  1 melinarozas  staff      786 Nov  8 12:30 figura_dominio.csv
-rw-r--r--@  1 melinarozas  staff      453 Nov  8 12:30 figura_edad.csv
-rw-r--r--@  1 melinarozas  staff      309 Nov  8 12:30 figura_region.csv
-rw-r--r--@  1 melinarozas  staff      207 Nov  8 12:30 figura_sexo.csv
-rw-r--r--@  1 melinarozas  staff      257 Nov  8 12:30 figura_sexo_jefe.csv
-rw-r--r--@  1 melinarozas  staff     9074 Nov  8 12:23 indicadores.csv
-rw-r--r--@  1 melinarozas  staff  1318454 Nov  8 12:23 personas_2024.parquet
-rw-r--r--@  1 melinarozas  staff     1299 Nov  8 12:27 pruebas_mcp.txt
-rw-r--r--@  1 melinarozas  staff     5242 Nov  8 12:23 validacion.txt
-rw-r--r--@  1 melinarozas  staff     1068 Nov  8 12:24 validacion_mapa.txt
```

</details>

**Claude:**

The zip files exist. I'll run the script as the skill instructs.

**→ Herramienta `Bash`**

```json
{
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/limpiando-enaho/scripts/limpiar.py; echo \"EXIT=$?\"",
 "description": "Run ENAHO cleaning and validation script",
 "timeout": 600000
}
```

<details><summary>Resultado</summary>

```text
Leídos 966-Modulo34/sumaria-2024.dta: 33,691 hogares y 966-Modulo02/enaho01-2024-200.dta: 117,721 personas
VALIDACIÓN ENAHO 2024 · generado 2026-11-08 12:31
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
… [recortado: 2297 caracteres más]
```

</details>

**→ Herramienta `Grep`**

```json
{
 "pattern": "^|Cusco|Cuzco|^.*,08,",
 "path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/indicadores.csv",
 "output_mode": "content",
 "-i": true,
 "head_limit": 3
}
```

<details><summary>Resultado</summary>

```text
1:anio,dimension,codigo,categoria,pobreza_pct,ee,ic_inf,ic_sup,cv_pct,n_muestra,poblacion_expandida,pobreza_pct_metodo_inei,indicador,fuente
2:2024,nacional,PE,Perú,27.5287,0.5194,26.5107,28.5467,1.8900,108664,34147766,27.5795,pobreza_monetaria,"INEI, ENAHO 2024 (módulos 34 y 02); cálculo propio ponderado con facpob07"
3:2024,area,Rural,Rural,39.4417,0.8477,37.7803,41.1031,2.1500,36071,6486385,39.3028,pobreza_monetaria,"INEI, ENAHO 2024 (módulos 34 y 02); cálculo propio ponderado con facpob07"

[Showing results with pagination = limit: 3]
```

</details>

**→ Herramienta `Grep`**

```json
{
 "pattern": "cusco|cuzco",
 "path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/indicadores.csv",
 "output_mode": "content",
 "-i": true
}
```

<details><summary>Resultado</summary>

```text
32:2024,departamento,08,Cusco,18.5393,2.0120,14.5958,22.4828,10.8500,3777,1380357,18.5413,pobreza_monetaria,"INEI, ENAHO 2024 (módulos 34 y 02); cálculo propio ponderado con facpob07"
```

</details>

**Claude:**

Según la ENAHO 2024, **la pobreza monetaria de Cusco en 2024 fue de 18.5 % de la población**.

- **Margen de error:** entre 14.6 % y 22.5 % (intervalo de confianza al 95 %). Es un margen amplio porque la muestra de un solo departamento es chica: 3,777 personas, que representan a 1,380,357 habitantes. La precisión es aceptable: el coeficiente de variación es 10.9 %.
- **Comprobación:** calculé la cifra de dos formas. Ponderando a cada persona con el factor de expansión (`facpob07`) sale 18.54 %. Con el método oficial del INEI, que usa el módulo de hogares, sale 18.54 % también.
- **Comparación:** está por debajo del promedio nacional, que fue 27.5 %. Los dos intervalos no se cruzan, así que la diferencia es clara.
- **Período y fuente:** año 2024, INEI, ENAHO 2024 (módulos 34 y 02). El cálculo es propio y sale de `salidas/indicadores.csv`, fila del departamento 08 (Cusco).
- **Validación:** antes de calcular corrí el script de limpieza de la ENAHO, que revisa los datos. Pasó las 22 verificaciones y reproduce la pobreza nacional oficial: 27.53 % frente al 27.6 % del INEI (`salidas/validacion.txt`).

No comparé el 18.5 % con la cifra que publica el INEI para Cusco porque no tengo esa referencia en el proyecto y no quiero darla de memoria.

RESPUESTA: 18.5

## Cierre

- Estado: success · turnos: 7 · duración: 22.1 s · costo estimado: US$ 0.17

