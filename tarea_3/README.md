# Tarea 3 – El Perú se calienta. La lluvia cuenta otra historia.

**Pregunta de investigación:** ¿qué departamentos del Perú se han calentado más desde 1981 y dónde ha cambiado más la lluvia?

| Producto | Enlace |
|---|---|
| Dashboard público | https://serugiran96.github.io/diplomado_pucp_tareas_melinarozas/ |
| Publicación de LinkedIn | PENDIENTE_LINKEDIN |
| Reel | [`reel/`](reel/) |

> **Estado del reel:** borrador con voz provisional del sistema (`reel/reel_borrador.mp4`); falta generar la narración con la voz de la autora.

## Descripción

El proyecto compara 45 años de temperatura y lluvia en los 25 departamentos del Perú (incluye Callao), de 1981 a 2025, y comprueba cada resultado con una segunda fuente independiente. Tiene dos productos: un dashboard interactivo con un mapa, seis gráficos, seis indicadores y siete filtros, y un reel vertical que resume los hallazgos.

## Tres hallazgos

1. **El calentamiento nacional es sólido.** La temperatura sube 0.22 °C por década (IC 95 %: ±0.10), o 0.50 °C entre 1981-2000 y 2006-2025. ERA5 da casi lo mismo: 0.21 °C por década y 0.46 °C. En ambas fuentes, 2024 y 2023 son los dos años más cálidos. Suben los 25 departamentos en NASA POWER y 22 de 25 en ERA5.
2. **El ritmo es desigual, y el orden depende de la fuente.** En NASA POWER, Ucayali lidera (+0.47 °C por década) e Ica es el último (+0.10). Ucayali también supera el promedio en ERA5 (+0.30), pero allí es séptimo y Puno encabeza (+0.41). La correlación de rangos entre fuentes es 0.41. Lo más estable es el otro extremo: Ica, Callao, Piura y Lambayeque están entre los que menos suben en ambas.
3. **La lluvia solo cae con claridad en el norte.** El total nacional casi no cambia (−0.8 %, no significativo). Solo Piura, Tumbes y Lambayeque caen más de 10 % en ambas fuentes (de −22 % a −41 %), y ningún departamento sube más de 10 % en ambas. Parte de la caída viene de los El Niño extremos: sin 1983, 1998, 2017 y 2023, Piura y Tumbes siguen bajando al menos 17 %, pero Lambayeque baja solo 7 % en ERA5.

Los aumentos de lluvia en Ica (+89 %) o Ayacucho (+47 %) aparecen en NASA POWER, pero no en ERA5 (+8 % y −3 %). Por eso no se presentan como hallazgos.

## Fuentes de datos

| Fuente | Uso | Descarga |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/), API mensual (MERRA-2) | Serie principal: temperatura media, máxima, mínima y lluvia | 1 de noviembre de 2026 |
| [ERA5 vía Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api), `models=era5` | Contraste independiente de temperatura y lluvia | 1 de noviembre de 2026 |
| [peru-geojson](https://github.com/juaneladio/peru-geojson) (MPL 2.0) | Límites departamentales | 1 de noviembre de 2026 |

Los datos usados están en [`datos/originales/`](datos/originales/). Las fechas exactas de descarga están en `registro_descarga.json`.

## Metodología

1. **Obtención:** 431 puntos de una malla de 0.5° dentro de los departamentos, con datos mensuales de 1981 a 2025 (252,135 filas crudas).
2. **Limpieza:** se descartan las 19,395 filas de resumen anual de la API (mes 13) y se buscan duplicados, faltantes (-999) y valores imposibles. No se encontró ninguno de estos tres (`datos/procesados/control_calidad.json`).
3. **Agregación:** promedio de las celdas de cada departamento, ponderado por área. Resultan 13,500 observaciones de departamento por mes. La lluvia diaria media se convierte en acumulado mensual. El valor nacional cuenta cada celda una vez.
4. **Indicadores:** tendencia lineal por década con IC 95 %, Theil-Sen y Mann-Kendall con corrección de Benjamini-Hochberg, cambio entre 1981-2000 y 2006-2025, y anomalías frente a la normal 1991-2020.
5. **Contraste:** ERA5 en un punto interior de cada departamento frente a NASA POWER. Se fija `models=era5` porque la opción por defecto de la API puede combinar varios modelos; una primera descarga con esa opción dio resultados distintos y se descartó.
6. **Sensibilidad:** se repite la caída de lluvia del norte sin los años de El Niño extremo.

El dashboard recalcula tendencias, cambios y KPI en el navegador a partir de los datos mensuales. Sus resultados iniciales coinciden con los de Python.

## Limitaciones

- NASA POWER y ERA5 son reanálisis de baja resolución, no estaciones. Este trabajo no usa datos del SENAMHI.
- La lluvia es la variable más débil: los productos difieren incluso en el nivel (en Áncash, unos 2,000 mm al año en ERA5 frente a unos 380 mm en NASA POWER).
- ERA5 se consultó en un solo punto por departamento por los límites de la API. Sirve mejor para comparar el sentido del cambio que su valor exacto.
- Una celda promedia valles y cumbres. Callao se representa con un solo punto, de casi 1,200 m de altitud de celda.
- El Niño de 1983 y 1998 pesa en el primer periodo, y 2023-2024 pesa al final de la serie.
- Costa, sierra y selva son una agrupación propia por región predominante.
- El análisis describe tendencias; no atribuye causas.

## Estructura

```
tarea_3/
├── datos/originales/    datos descargados y registro de descarga
├── datos/procesados/    tablas limpias, indicadores, contrastes y resultados.json
├── scripts/             obtener_datos, procesar_datos, analizar_datos, obtener_fotos, capturar_dashboard
├── web/                 dashboard (index.html, assets/, data/)
├── reel/                guion.json, narrar, construir_reel, verificar_guion, subtítulos y recursos/
└── linkedin/            borrador de la publicación y capturas
```

## Cómo reproducirlo

Requiere [uv](https://docs.astral.sh/uv/). La captura del dashboard usa Google Chrome.

```bash
cd tarea_3
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

.venv/bin/python scripts/obtener_datos.py      # descarga; ERA5 puede tardar por el límite por hora de la API
.venv/bin/python scripts/procesar_datos.py
(cd scripts && ../.venv/bin/python analizar_datos.py)
.venv/bin/python -m http.server 8000 --directory web   # dashboard en http://localhost:8000
.venv/bin/python scripts/capturar_dashboard.py         # prueba los controles y genera capturas
```

Reel, con un entorno aparte para la voz (la primera corrida baja unos 4 GB de modelos):

```bash
uv venv --python 3.12 .venv-voz
uv pip install --python .venv-voz/bin/python -r requirements-voz.txt
bash reel/finalizar_reel.sh RUTA_A_TU_AUDIO
```

La narración sigue el flujo de la [Sesión 15](https://github.com/d2cml-ai/Data-Science-Python/tree/main/sessions/15-texto-a-reel): Qwen3-TTS para clonar la voz y Whisper para subtítulos y control de calidad. `reel/verificar_guion.py` comprueba las afirmaciones del guion contra los datos.

## Créditos del reel

- **Fotos:** [río Ucayali](https://commons.wikimedia.org/wiki/File:The_Ucayali_River_in_the_lowland_Amazon_rainforest_of_central_Peru_(iss074e0492148).jpg) y [Andes](https://commons.wikimedia.org/wiki/File:ISS-59_Andes_mountain_range,_Peru.jpg), NASA (dominio público); [desierto de Ica](https://commons.wikimedia.org/wiki/File:Desert_-_Ica_-_panoramio.jpg), Pavel Špindler (CC BY 3.0).
- **Música:** original, sintetizada con `reel/generar_musica.py` y liberada como CC0.
- **Tipografías:** Oswald y Public Sans (SIL Open Font License).
- **Voz:** generada con IA a partir de la voz de la autora.

## Uso de inteligencia artificial

Claude Code (Claude Opus 5.5, de Anthropic) propuso el tema y escribió el código del análisis, el dashboard, el guion y el montaje del reel, además de este README. Qwen3-TTS genera la narración y Whisper, los subtítulos. Las cifras se calculan desde los datos con los scripts del repositorio y las afirmaciones del guion se comprueban con `verificar_guion.py`. La autora es responsable de la revisión final de los productos.
