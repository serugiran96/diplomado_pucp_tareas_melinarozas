---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza monetaria (o extrema) por departamento del Perú con la ENAHO 2024 del INEI, uniendo indicadores y geometrías por código territorial (ubigeo[:2] = FIRST_IDDP) y comparando con la referencia oficial. Úsala cuando pidan un mapa, mapear, ver en el territorio o comparar regiones o departamentos de la pobreza con la ENAHO. Si no existe la base procesada, primero usa limpiando-enaho.
argument-hint: "[--indicador pobre|pobre_extremo]"
---

# Mapear la pobreza de la ENAHO 2024 por departamento

## Pasos

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill **limpiando-enaho** y espera a que su
   validación apruebe. Si el script responde `FALTA LA BASE` (código 2), es la misma señal.
2. Corre desde la raíz del proyecto:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py                          # pobreza monetaria
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --indicador pobre_extremo  # pobreza extrema
   ```

   El GeoJSON departamental del curso se baja solo a `datos/` si no está.
3. Lee `salidas/validacion_mapa.txt`. Debe decir 25 departamentos unidos con dato y Lima y Callao separados.
   Si la unión deja algún departamento sin dato, el script termina con error: informa eso, no lo tapes.
4. Responde con la ruta `mapas/pobreza_departamento.png`, los tres departamentos más y menos pobres
   (impresos por el script) y el resultado de la comparación con la referencia de la Sesión 16
   (`salidas/comparacion_mapa_referencia.csv`).

## Reglas que el script ya cumple

- Une por código, nunca por nombre: `ubigeo[:2]` con `FIRST_IDDP`, ambos como texto de dos dígitos, con
  `validate="one_to_one"`. «APURIMAC» no es «Apurímac»; el código no tiene ese problema.
- 25 unidades con dato; Lima (15) y Callao (07) separados (Callao lleva etiqueta con línea porque es pequeño).
- Escala de un solo tono (OrRd), de claro a oscuro, desde 0; leyenda con la unidad: % de personas.
- Compara cada departamento con `referencias/pobreza_departamento_2024.csv` con los dos métodos de
  ponderación (ver `../limpiando-enaho/reference.md`): método INEI ≤ 0.1 pp; base de personas dentro del IC 95 %.
