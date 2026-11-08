# Referencia: ENAHO 2024 en este proyecto

## Archivos de origen

| Módulo | Archivo dentro del zip | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|---|
| 34, sumaria | `966-Modulo34/sumaria-2024.dta` | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` |
| 02, miembros | `966-Modulo02/enaho01-2024-200.dta` | persona | 117,721 | las tres + `codperso` | `facpob07` |

Descarga: `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo{34,02}.zip`.
El zip del módulo 34 trae también `sumaria-2024-12g.dta` (gasto en 12 grupos); el script usa `sumaria-2024.dta`.

## Reglas del pipeline (`scripts/limpiar.py`)

1. **Lectura**: `pd.read_stata(..., convert_categoricals=False)`; las llaves se fuerzan a texto con su largo
   (`conglome` 6, `vivienda` 3, `hogar` 2, `codperso` 2, `ubigeo` 6) para no perder ceros iniciales.
2. **Nombres**: minúsculas y sin tildes; `aÑo` pasa a `anio`.
3. **Residentes habituales**: `((p204 == 1) & (p205 == 2)) | ((p204 == 2) & (p206 == 1))`
   - `p204`: ¿es miembro del hogar? (1 sí, 2 no) · `p205`: ¿estuvo ausente 30 días o más? (1 sí, 2 no) ·
     `p206`: ¿estuvo presente 30 días o más? (1 sí, 2 no).
4. **Unión**: `personas.merge(sumaria, on=[conglome, vivienda, hogar], how="left", validate="m:1")`; se verifica
   que no cambie el número de filas, que todas las personas tengan hogar y que la persona siga siendo única.
5. **Variables construidas**

| Variable | Definición |
|---|---|
| `departamento` | `ubigeo[:2]` (texto, 01-25; Lima 15 y Callao 07 separados) |
| `area` | `Urbana` si `estrato <= 5`, `Rural` si `estrato >= 6` |
| `pobre` | 1 si `pobreza <= 2` (pobre extremo o no extremo) |
| `pobre_extremo` | 1 si `pobreza == 1` |
| `sexo` | `p207`: 1 Hombre, 2 Mujer |
| `sexo_jefe` | sexo de la persona con `p203 == 1` (jefe o jefa) en el hogar |
| `grupo_edad` | `p208a` en 0-14, 15-29, 30-44, 45-64, 65+ |
| `dominio_nombre` | 1 Costa norte, 2 Costa centro, 3 Costa sur, 4 Sierra norte, 5 Sierra centro, 6 Sierra sur, 7 Selva, 8 Lima Metropolitana |
| `region_natural` | Costa (dominios 1, 2, 3, 8), Sierra (4, 5, 6), Selva (7) |

`pobreza` en la sumaria: 1 pobre extremo, 2 pobre no extremo, 3 no pobre.

## Ponderación y error estándar

- Toda proporción es `sum(facpob07 * y) / sum(facpob07)` sobre los residentes habituales. Para ellos,
  `facpob07` es igual a `factor07` (se comprobó: razón 1.0 en las 108,664 filas).
- El error estándar usa linealización de Taylor con conglomerados (`conglome`) dentro de estratos (`estrato`),
  como `svyset conglome [pw=facpob07], strata(estrato)`. El diseño oficial del INEI tiene estratos más finos,
  así que estos intervalos pueden ser algo más anchos que los publicados (son conservadores).

## Dos métodos, una diferencia explicada

| Método | Población que cuenta | Pobreza nacional 2024 |
|---|---|---|
| Base de personas + `facpob07` (el del proyecto) | residentes habituales según el filtro de arriba (108,664) | 27.53 % |
| Sumaria + `factor07 × mieperho` (el de las cifras oficiales del INEI) | `mieperho`, miembros del hogar según el INEI | 27.58 % |

En el 94.5 % de los hogares, el número de residentes coincide con `mieperho`; en el resto no (por ejemplo,
`mieperho` excluye a trabajadores del hogar y pensionistas). Por eso, en subgrupos pequeños las dos cifras
difieren unas décimas (rural +0.14 pp, Lima Metropolitana −0.18 pp, Huánuco +0.5 pp). `indicadores.csv` trae
las dos (`pobreza_pct` y `pobreza_pct_metodo_inei`). Las referencias del curso (Sesión 16) se reproducen con el
método del INEI con diferencia ≤ 0.1 pp, y caen dentro del IC 95 % de la base de personas en los 25 departamentos.

## Salidas

`salidas/indicadores.csv`: `anio, dimension, codigo, categoria, pobreza_pct, ee, ic_inf, ic_sup, cv_pct,
n_muestra, poblacion_expandida, pobreza_pct_metodo_inei, indicador, fuente`. Las dimensiones son `nacional`,
`area`, `sexo`, `sexo_jefe_hogar`, `grupo_edad`, `region_natural`, `dominio`, `departamento` y
`pobreza_extrema_nacional`.

## Códigos de departamento

01 Amazonas · 02 Áncash · 03 Apurímac · 04 Arequipa · 05 Ayacucho · 06 Cajamarca · 07 Callao · 08 Cusco ·
09 Huancavelica · 10 Huánuco · 11 Ica · 12 Junín · 13 La Libertad · 14 Lambayeque · 15 Lima · 16 Loreto ·
17 Madre de Dios · 18 Moquegua · 19 Pasco · 20 Piura · 21 Puno · 22 San Martín · 23 Tacna · 24 Tumbes · 25 Ucayali
