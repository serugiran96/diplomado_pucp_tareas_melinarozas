# Tarea 1 – Noticias peruanas: del titular al clasificador

## 1. Pregunta del proyecto
**¿Pueden convertir titulares peruanos en un clasificador de noticias?** Se recolectan titulares reales, se normalizan a 4 categorías (`politica`, `economia`, `deportes`, `ciencia_tecnologia`), se etiquetan con un LLM como supervisión débil, se ajusta un Transformer ligero y se despliega un dashboard que clasifica titulares nuevos en vivo.

## 2. Medios y fechas de extracción
- **Opción C – Comparada:** La República (https://larepublica.pe) y El Comercio (https://elcomercio.pe).
- **Fecha de descarga:** 18 de octubre de 2026 (hora de Lima). El detalle de inicio y fin, el User-Agent, las pausas y el número de solicitudes está en `datos/raw/metadata_descarga.json`.
- **Fuentes:** RSS oficiales, sitemaps (*news* y *web*) y portadas de sección. Todas están permitidas por el `robots.txt` de cada medio. En La República, además, se siguen enlaces internos entre artículos de la misma sección (ver limitaciones).
- **Buenas prácticas:** User-Agent descriptivo, pausa aleatoria de 1–2 s después de cada solicitud, máximo 1 reintento y un hilo por dominio. Cada URL se valida contra el `robots.txt`.

## 3. Hallazgos analíticos
Datos: 440 noticias, 55 por medio y categoría; todas las URLs respondieron HTTP 200 al descargarlas. Los detalles están en `01_recoleccion.ipynb`.

1. **La República titula más largo; El Comercio, con más dispersión.**
   - Mediana: 104 caracteres en La República frente a 97 en El Comercio.
   - El Comercio concentra los dos extremos: columnas de opinión de economía con titulares de 23–43 caracteres y poca señal temática (por ejemplo, "AlaCena no tiene precio"), y citas textuales de hasta 178 caracteres en deportes y política.
   - Esos titulares tan cortos son los candidatos más claros a error de clasificación.
2. **Los medios difieren en profundidad temporal.**
   - El Comercio: noticias del 9 al 18 de octubre de 2026 (mediana, el 16).
   - La República: mediana el 12 de octubre, con notas que llegan hasta 2019, porque su contenido accesible se limita a ~48 h y el resto proviene de enlaces internos.
   - De 682 URLs únicas descubiertas, 236 (35 %) eran de secciones fuera de las 4 categorías, sobre todo `sociedad`, `mundo`, `espectaculos` y `mag`. Esas noticias se descartaron.

## 4. Limitaciones técnicas
1. **Ventana corta en La República.** Sus RSS y sitemaps solo cubren unas 48 horas, y su `robots.txt` prohíbe el archivo (`/archivo/*`) y la paginación (`/*/pag/*`). Para llegar a ~50 noticias por categoría se siguieron los enlaces internos que cada artículo publica hacia notas de su misma sección. Por eso las fechas de La República abarcan un rango más amplio que las de El Comercio, y la muestra no es aleatoria: depende de qué notas enlaza el propio medio.
2. **La etiqueta de referencia viene de la sección del medio, no de una anotación humana.** Algunas notas cruzan temas (por ejemplo, presupuesto público entre `politica` y `economia`), así que la referencia tiene ruido y limita el F1 alcanzable. Además, el modelo usa solo el titular, porque es lo que recibe el dashboard.

## 5. Ejecución en local
```bash
cd tarea_1
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Parte 1: reconstruye todo desde datos/raw/ (FORZAR_DESCARGA=True para volver a descargar)
jupyter nbconvert --to notebook --execute --inplace 01_recoleccion.ipynb

# Parte 2: el LLM es local (Qwen2.5-0.5B-Instruct, sin API de pago). Si falta datos/etiquetas_llm.csv,
# el notebook ejecuta llm_etiquetado.py (≈5 min en CPU). Alternativas: LLM_BACKEND=gemini u ollama
HF_HUB_DISABLE_XET=1 jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb

# Parte 3: dashboard
streamlit run app.py
```
La exportación de gráficos a PNG (`kaleido`) requiere Google Chrome instalado (o ejecutar `plotly_get_chrome`).

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb      # Scraping (RSS + sitemaps), limpieza, mapeo, descartes y EDA
├── 02_clasificacion.ipynb    # Zero-shot, LLM débil + auditoría, split 70/15/15, fine-tuning y evaluación
├── llm_etiquetado.py         # Supervisión débil con LLM local (Qwen2.5-0.5B-Instruct)
├── app.py                    # Dashboard Streamlit
├── requirements.txt
├── datos/
│   ├── noticias.csv          # Dataset final (7 columnas)
│   ├── etiquetas_llm.csv     # Etiquetas del LLM: titular, etiqueta_llm, confianza, modelo_llm, fecha
│   ├── auditoria_llm_20.csv  # 20 predicciones del LLM revisadas manualmente (etiqueta_humana)
│   └── raw/                  # Respaldo crudo: robots.txt, feeds/sitemaps (.gz), candidatos y metadatos por artículo
├── graficos/                 # PNG de los gráficos (visibles en GitHub)
└── modelo/                   # metricas.json, config y tokenizer; los pesos (.safetensors) no se suben
```

## Resultados de la clasificación (`02_clasificacion.ipynb`)
| Enfoque | Evaluado en | Accuracy | F1 macro |
|---|---|---|---|
| Zero-shot (`Recognai/bert-base-spanish-wwm-cased-xnli`) | 40 titulares de test | 0.700 | 0.682 |
| LLM débil (`Qwen/Qwen2.5-0.5B-Instruct`, local) | 66 titulares de test | 0.394 | 0.283 |
| **DistilBERT multilingüe fine-tuned** | 66 titulares de test | **0.848** | **0.852** |

- **Auditoría humana del LLM:** 12/20 coincidencias (60 %).
- **Split:** estratificado 70/15/15 con `random_state=42`.
- **Matriz de confusión:** `graficos/04_matriz_confusion_test.png`. El error principal es la confusión entre `politica` y `economia` (4 en cada sentido).

**¿Por qué el LLM clasificó noticias deportivas como economía?** El modelo de 0.5B colapsa hacia `economia`: predijo esa etiqueta en 376 de 440 titulares y nunca eligió `politica` ni `deportes`. Hay tres causas probables:
- **Tamaño del modelo:** sigue mal instrucciones de clasificación en español y, ante la duda, cae en una etiqueta por defecto. En los titulares deportivos la confianza mediana fue de 0.71, frente a 0.96 en los económicos.
- **Método de puntuación:** solo se compara el primer token de cada categoría, y los nombres se tokenizan de forma desigual (`polit`, `e`, `de`, `ci`). El token genérico `e` favorece a `economia`.
- **Señales léxicas engañosas:** marcadores, fechas y nombres comerciales ("ESPN Premium") que un modelo pequeño asocia a mercados.

DistilBERT, con supervisión, obtiene F1 = 1.00 en `deportes`. El detalle está en la sección 2.2 del notebook.

## Estado de avance (19/10/2026)
- **Parte 1 – completa:** notebook ejecutado, 440 noticias, 3 gráficos Plotly (PNG en `graficos/`) y respaldo crudo en `datos/raw/`.
- **Parte 2 – completa:** notebook ejecutado con zero-shot, etiquetas LLM, auditoría de 20 casos, split, fine-tuning, métricas en test, tabla comparativa y justificación.
- **Parte 3 – completa en local:** `streamlit run app.py` muestra filtros, las 3 métricas, el gráfico, la tabla con descarga y el probador en vivo.
  - Los pesos (`modelo/model.safetensors`, 516 MB) no se suben a GitHub. En otra máquina, ejecutar `02_clasificacion.ipynb` regenera el modelo.
  - No se desplegó en Streamlit Cloud (opcional).
