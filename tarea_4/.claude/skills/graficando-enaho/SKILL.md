---
name: graficando-enaho
description: Genera gráficos de barras de la pobreza monetaria o extrema del Perú con la ENAHO 2024 del INEI, ponderados y con intervalos de confianza, por área urbana y rural, sexo, sexo del jefe de hogar, grupo de edad, región natural (costa, sierra, selva), dominio o departamento. Úsala cuando pidan graficar, visualizar o comparar en un gráfico la pobreza o las brechas de la ENAHO. Si no existe la base procesada, primero usa limpiando-enaho.
argument-hint: "[area|sexo|sexo_jefe|edad|region|dominio|departamento|todos]"
---

# Graficar la pobreza de la ENAHO 2024

## Pasos

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho** y espera a que su
   validación apruebe. Si el script de abajo responde `FALTA LA BASE` (código 2), es la misma señal.
2. Traduce el pedido a un `--tipo`:

| Si piden... | `--tipo` |
|---|---|
| urbano y rural, campo y ciudad, área de residencia | `area` |
| hombres y mujeres, sexo, género | `sexo` |
| hogares con jefa mujer o jefe hombre | `sexo_jefe` |
| niños, jóvenes, adultos mayores, edad | `edad` |
| costa, sierra y selva, región natural | `region` |
| dominios geográficos, Lima Metropolitana frente al resto | `dominio` |
| departamentos, regiones, comparación territorial | `departamento` |
| todo lo anterior | `todos` |

   Si piden pobreza extrema, agrega `--indicador pobre_extremo`. Si el pedido es `$ARGUMENTS`, úsalo como tipo.
3. Corre desde la raíz del proyecto:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --tipo area
   ```

4. El script imprime el título analítico y la tabla graficada, y guarda `figuras/pobreza_<tipo>.png` y
   `salidas/figura_<tipo>.csv`. Responde con la ruta de la figura y las cifras de esa tabla (no de memoria).
5. Interpreta con cuidado: si el título dice que la diferencia está dentro del margen de error, no la
   presentes como brecha. Describe asociaciones, no causas.

## Reglas que el script ya cumple (no las rompas si lo modificas)

- Estimación ponderada con `facpob07`; barras desde cero; un solo color; valor escrito en cada barra.
- Título que dice qué muestra con las cifras; subtítulo con indicador, grupo, año y unidad (% de personas).
- Línea punteada con el promedio nacional e intervalos de confianza al 95 %.
- Nota «Fuente: INEI, ENAHO 2024 (módulos 34 y 02)». PNG a 200 dpi en `figuras/`.
