# Demo 1 · Un pedido en lenguaje natural activa limpiando-enaho y luego mapeando-enaho

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
Haz un mapa de la pobreza monetaria por departamento con ENAHO 2024.
```

## Sesión

**→ Herramienta `Skill`**

```json
{
 "skill": "mapeando-enaho"
}
```

<details><summary>Resultado</summary>

```text
Launching skill: mapeando-enaho
```

</details>

**→ Herramienta `Bash`**

```json
{
 "command": "ls salidas/ datos/ mapas/ 2>&1 | head -50",
 "description": "Check for processed base and outputs"
}
```

<details><summary>Resultado</summary>

```text
datos/:
966-Modulo02.zip
966-Modulo34.zip
bcrp
peru_departamental_simple.geojson

mapas/:
pobreza_departamento.png

salidas/:
comparacion_mapa_referencia.csv
figura_area.csv
figura_departamento.csv
figura_dominio.csv
figura_edad.csv
figura_region.csv
figura_sexo.csv
figura_sexo_jefe.csv
indicadores.csv
pruebas_mcp.txt
validacion.txt
validacion_mapa.txt
```

</details>

**Claude:**

No existe `salidas/personas_2024.parquet`, así que primero corro la limpieza.

**→ Herramienta `Skill`**

```json
{
 "skill": "limpiando-enaho"
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
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/limpiando-enaho/scripts/limpiar.py; echo \"EXIT=$?\"",
 "description": "Run ENAHO cleaning and validation script",
 "timeout": 600000
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
 "timeout": 600000
}
```

<details><summary>Resultado</summary>

```text
Leídos 966-Modulo34/sumaria-2024.dta: 33,691 hogares y 966-Modulo02/enaho01-2024-200.dta: 117,721 personas
VALIDACIÓN ENAHO 2024 · generado 2026-11-08 12:19
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

**Claude:**

La validación aprobó (22/22). Ahora el mapa.

**→ Herramienta `Bash`**

```json
{
 "command": "uv run ~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/.claude/skills/mapeando-enaho/scripts/mapear.py",
 "description": "Generate department poverty choropleth map",
 "timeout": 600000
}
```

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/validacion_mapa.txt"
}
```

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/salidas/comparacion_mapa_referencia.csv"
}
```

<details><summary>Resultado</summary>

```text
VALIDACIÓN DEL MAPA · Pobreza monetaria, ENAHO 2024
Mapa: mapas/pobreza_departamento.png

[OK] Unidades territoriales en el GeoJSON: 25 (referencia: 25) APROBADA
[OK] Departamentos unidos con dato (ubigeo[:2] = FIRST_IDDP): 25 (referencia: 25) APROBADA
[OK] Lima (15) y Callao (07) como unidades separadas: CALLAO, LIMA (referencia: CALLAO, LIMA) APROBADA
[OK] Máx. diferencia con la referencia, método INEI (sumaria): 0.0 pp (referencia: <= 0.1 pp) APROBADA
[OK] Máx. diferencia con la referencia, base de personas (facpob07): 0.5 pp (Huánuco) (referencia: <= 0.6 pp) APROBADA
[OK] Referencia dentro del IC 95 % de la estimación: 25/25 (referencia: 25/25) APROBADA
[OK] Mismo departamento con mayor y menor pobreza que la referencia: Cajamarca / Ica (referencia: Cajamarca / Ica) APROBADA

Comparación completa en salidas/comparacion_mapa_referencia.csv. La referencia del curso se calculó con la sumaria (factor07 × mieperho); la base de personas cuenta a los residentes habituales, por eso hay diferencias de algunas décimas, siempre dentro del IC 95 %.
FIRST_IDDP       NOMBDEP     pct  ic_inf  ic_sup
        06     CAJAMARCA 44.9950 40.5022 49.4877
        16        LORETO 42.6051 38.0651 47.1451
        21          PUNO 40.4177 35.7940 45.0414
        10       HUANUCO 39.4729 34.2587 44.6870
        19         PASCO 39.2818 34.3427 44.2210
        07        CALLAO 33.7683 29.0972 38.4395
        09  HUANCAVELICA 33.6082 29.0417 38.1746
        05      AYACUCHO 33.0398 28.4166 37.6630
        20         PIURA 31.8118 28.5092 35.1144
        13   LA LIBERTAD 30.0745 26.3616 33.7875
        25       UCAYALI 27.1231 22.8031 31.4431
        15          LIMA 26.8888 24.5363 29.2412
        24        TUMBES 26.5968 21.8010 31.3926
        01      AMAZONAS 26.0808 21.1921 30.9695
        03      APURIMAC 24.0880 19.5030 28.6729
        23         TACNA 23.8832 18.2986 29.4679
        02        ANCASH 22.8814 19.0045 26.7583
        22    SAN MARTIN 21.9938 18.0925 25.8951
        12         JUNIN 18.6104 14.8872 22.3336
        08         CUSCO 18.5393 14.5958 22.4828
        04      AREQUIPA 15.7674 12.5837 18.9512
        14    LAMBAYEQUE 14.0526 10.2905 17.8146
        17 MADRE DE DIOS 11.1359  6.9451 15.3268
        18      MOQUEGUA 10.8781  7.3157 14.4405
        11           ICA  5.9139  4.1240  7.7038
```

</details>

<details><summary>Resultado</summary>

```text
1	VALIDACIÓN DEL MAPA · Pobreza monetaria, ENAHO 2024
2	Mapa: mapas/pobreza_departamento.png
3	
4	[OK] Unidades territoriales en el GeoJSON: 25 (referencia: 25) APROBADA
5	[OK] Departamentos unidos con dato (ubigeo[:2] = FIRST_IDDP): 25 (referencia: 25) APROBADA
6	[OK] Lima (15) y Callao (07) como unidades separadas: CALLAO, LIMA (referencia: CALLAO, LIMA) APROBADA
7	[OK] Máx. diferencia con la referencia, método INEI (sumaria): 0.0 pp (referencia: <= 0.1 pp) APROBADA
8	[OK] Máx. diferencia con la referencia, base de personas (facpob07): 0.5 pp (Huánuco) (referencia: <= 0.6 pp) APROBADA
9	[OK] Referencia dentro del IC 95 % de la estimación: 25/25 (referencia: 25/25) APROBADA
10	[OK] Mismo departamento con mayor y menor pobreza que la referencia: Cajamarca / Ica (referencia: Cajamarca / Ica) APROBADA
11	
12	Comparación completa en salidas/comparacion_mapa_referencia.csv. La referencia del curso se calculó con la sumaria (factor07 × mieperho); la base de personas cuenta a los residentes habituales, por eso hay diferencias de algunas décimas, siempre dentro del IC 95 %.
13	
```

</details>

<details><summary>Resultado</summary>

```text
1	departamento,nombre_referencia,referencia,nombre,pct,ic_inf,ic_sup,pct_metodo_inei,dif_personas,dif_metodo_inei,referencia_en_ic95
2	01,AMAZONAS,25.7000,Amazonas,26.0808,21.1921,30.9695,25.7488,0.4000,0.0000,True
3	02,ANCASH,22.8000,Áncash,22.8814,19.0045,26.7583,22.7746,0.1000,0.0000,True
4	03,APURIMAC,24.0000,Apurímac,24.0880,19.5030,28.6729,23.9587,0.1000,0.0000,True
5	04,AREQUIPA,15.8000,Arequipa,15.7674,12.5837,18.9512,15.7844,0.0000,0.0000,True
6	05,AYACUCHO,32.8000,Ayacucho,33.0398,28.4166,37.6630,32.7633,0.2000,0.0000,True
7	06,CAJAMARCA,45.0000,Cajamarca,44.9950,40.5022,49.4877,45.0069,0.0000,0.0000,True
8	07,CALLAO,33.9000,Callao,33.7683,29.0972,38.4395,33.8599,-0.1000,0.0000,True
9	08,CUSCO,18.5000,Cusco,18.5393,14.5958,22.4828,18.5413,0.0000,0.0000,True
10	09,HUANCAVELICA,33.4000,Huancavelica,33.6082,29.0417,38.1746,33.4034,0.2000,0.0000,True
11	10,HUANUCO,39.0000,Huánuco,39.4729,34.2587,44.6870,38.9626,0.5000,0.0000,True
12	11,ICA,6.0000,Ica,5.9139,4.1240,7.7038,6.0142,-0.1000,0.0000,True
13	12,JUNIN,18.5000,Junín,18.6104,14.8872,22.3336,18.4994,0.1000,0.0000,True
14	13,LA LIBERTAD,30.2000,La Libertad,30.0745,26.3616,33.7875,30.1903,-0.1000,0.0000,True
15	14,LAMBAYEQUE,14.0000,Lambayeque,14.0526,10.2905,17.8146,14.0406,0.1000,0.0000,True
16	15,LIMA,27.1000,Lima,26.8888,24.5363,29.2412,27.0689,-0.2000,0.0000,True
17	16,LORETO,43.0000,Loreto,42.6051,38.0651,47.1451,42.9726,-0.4000,0.0000,True
18	17,MADRE DE DIOS,11.1000,Madre de Dios,11.1359,6.9451,15.3268,11.1478,0.0000,0.0000,True
19	18,MOQUEGUA,11.0000,Moquegua,10.8781,7.3157,14.4405,10.9682,-0.1000,0.0000,True
20	19,PASCO,39.0000,Pasco,39.2818,34.3427,44.2210,38.9720,0.3000,0.0000,True
21	20,PIURA,31.9000,Piura,31.8118,28.5092,35.1144,31.8610,-0.1000,0.0000,True
22	21,PUNO,39.9000,Puno,40.4177,35.7940,45.0414,39.9381,0.5000,0.0000,True
23	22,SAN MARTIN,22.0000,San Martín,21.9938,18.0925,25.8951,22.0215,0.0000,0.0000,True
24	23,TACNA,24.0000,Tacna,23.8832,18.2986,29.4679,23.9890,-0.1000,0.0000,True
25	24,TUMBES,26.9000,Tumbes,26.5968,21.8010,31.3926,26.9012,-0.3000,0.0000,True
26	25,UCAYALI,27.1000,Ucayali,27.1231,22.8031,31.4431,27.0701,0.0000,0.0000,True
27	
```

</details>

**→ Herramienta `Read`**

```json
{
 "file_path": "~/Documents/GitHub/diplomado_pucp_tareas_melinarozas/tarea_4/mapas/pobreza_departamento.png"
}
```

<details><summary>Resultado</summary>

```text
[imagen]
```

</details>

**Claude:**

Hice el mapa: **`mapas/pobreza_departamento.png`**

Antes corrí la limpieza, porque no existía la base procesada (`salidas/personas_2024.parquet`). Pasó las 22 verificaciones. La pobreza nacional sale 27.5 % (IC 95 %: 26.5–28.6) con la base de personas y 27.6 % con el método del INEI, igual que la cifra oficial. Este mapa reemplaza al que ya había en `mapas/`.

**Unión con el mapa** (`salidas/validacion_mapa.txt`): los 25 departamentos se unieron por código (`ubigeo[:2] = FIRST_IDDP`) y todos tienen dato. Lima y Callao aparecen por separado.

**Departamentos más pobres** (% de personas, IC 95 %):
| Departamento | Pobreza | IC 95 % |
|---|---|---|
| Cajamarca | 45.0 | 40.5–49.5 |
| Loreto | 42.6 | 38.1–47.1 |
| Puno | 40.4 | 35.8–45.0 |

**Departamentos menos pobres:**
| Departamento | Pobreza | IC 95 % |
|---|---|---|
| Ica | 5.9 | 4.1–7.7 |
| Moquegua | 10.9 | 7.3–14.4 |
| Madre de Dios | 11.1 | 6.9–15.3 |

Dentro de cada grupo de tres, los intervalos se superponen. Por eso el orden entre ellos no es una diferencia clara: por ejemplo, no se puede decir que Cajamarca sea más pobre que Loreto. Lo que sí queda claro es la distancia entre los dos grupos.

**Comparación con la referencia de la Sesión 16** (`salidas/comparacion_mapa_referencia.csv`):
- **Método del INEI** (hogares × miembros): la diferencia es de 0.0 pp en los 25 departamentos.
- **Base de personas** (la que usa el mapa): la mayor diferencia es de 0.5 pp, en Huánuco (39.5 frente a 39.0) y en Puno. Las 25 cifras de referencia quedan dentro del IC 95 %. Las décimas de diferencia salen de contar solo a los residentes habituales.
- El departamento más pobre y el menos pobre son los mismos que en la referencia: Cajamarca e Ica.

Fuente: INEI, ENAHO 2024 (módulos 34 y 02), estimación ponderada con `facpob07`.

Si quieres el mapa de pobreza extrema, se hace con el mismo script agregando `--indicador pobre_extremo`.

## Cierre

- Estado: success · turnos: 12 · duración: 31.6 s · costo estimado: US$ 0.27

