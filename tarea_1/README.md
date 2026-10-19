# Tarea 1 – Noticias peruanas: del titular al clasificador

## 1. Pregunta del proyecto
**¿Pueden convertir titulares peruanos en un clasificador de noticias?** Se recolectan titulares reales, se normalizan a 4 categorías (`politica`, `economia`, `deportes`, `ciencia_tecnologia`), se etiquetan con un LLM como supervisión débil, se ajusta un Transformer ligero y se despliega un dashboard que clasifica titulares nuevos en vivo.

## 2. Medios y fechas de extracción
- **Opción C – Comparada:** La República (https://larepublica.pe) y El Comercio (https://elcomercio.pe).
- **Fecha de descarga:** 18 de octubre de 2026 (hora de Lima). El detalle de inicio y fin, el User-Agent, las pausas y el número de solicitudes está en `datos/raw/metadata_descarga.json`.
- **Fuentes:** RSS oficiales, sitemaps (*news* y *web*) y portadas de sección. Todas están permitidas por el `robots.txt` de cada medio. En La República, además, se siguen enlaces internos entre artículos de la misma sección (ver limitaciones).
- **Buenas prácticas:** User-Agent descriptivo, pausa aleatoria de 1–2 s después de cada solicitud, máximo 1 reintento y un hilo por dominio. Cada URL se valida contra el `robots.txt`.

## 3. Hallazgos analíticos
_Se completan con las salidas de `01_recoleccion.ipynb` (sección 3)._

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

# Parte 2: requiere GEMINI_API_KEY en tarea_1/.env (o LLM_BACKEND=ollama con Ollama local)
jupyter nbconvert --to notebook --execute --inplace 02_clasificacion.ipynb

# Parte 3: dashboard
streamlit run app.py
```
La exportación de gráficos a PNG (`kaleido`) requiere Google Chrome instalado (o ejecutar `plotly_get_chrome`).

## Estructura
```
tarea_1/
├── 01_recoleccion.ipynb      # Scraping (RSS + sitemaps), limpieza, mapeo, descartes y EDA
├── 02_clasificacion.ipynb    # Zero-shot, LLM débil + auditoría, split 70/15/15, fine-tuning y evaluación
├── app.py                    # Dashboard Streamlit
├── requirements.txt
├── datos/
│   ├── noticias.csv          # Dataset final (7 columnas)
│   ├── etiquetas_llm.csv     # Se genera en la Parte 2
│   └── raw/                  # Respaldo crudo: robots.txt, feeds/sitemaps (.gz), candidatos y metadatos por artículo
├── graficos/                 # PNG de los gráficos (visibles en GitHub)
└── modelo/                   # metricas.json, config y tokenizer; los pesos (.safetensors) no se suben
```

## Estado de avance
- **Parte 1:** ver Issue #1.
- **Parte 2:** el código de `02_clasificacion.ipynb` está preparado, pero **aún no se ejecutó**. No hay métricas, etiquetas LLM ni entrenamiento todavía. Para ejecutarlo hace falta:
  - una API key de Gemini (u Ollama local);
  - completar la auditoría humana en `datos/auditoria_llm_20.csv`.
- **Parte 3:** `app.py` está implementado. Hasta que exista el modelo entrenado, las métricas del modelo aparecen como "pendiente" y el probador en vivo avisa que falta el modelo.
