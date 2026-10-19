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

## Estado de avance (18/10/2026, 23:48)
- **Parte 1 – completa:**
  - `01_recoleccion.ipynb` ejecutado, con 440 noticias y 3 gráficos Plotly (PNG en `graficos/`).
  - Respaldo crudo en `datos/raw/`.
- **Parte 2 – parcial:** `02_clasificacion.ipynb` está ejecutado con resultados reales.
  - Zero-shot: F1 macro de 0.682 en 40 titulares de test.
  - Split estratificado 70/15/15 (`random_state=42`).
  - DistilBERT fine-tuned: F1 macro de **0.852** en test (66 titulares). La matriz de confusión está en `graficos/04_matriz_confusion_test.png`.
  - **Pendiente:**
    - el etiquetado con LLM (`datos/etiquetas_llm.csv`), porque falta `GEMINI_API_KEY` en `tarea_1/.env`;
    - la auditoría humana de 20 casos (`datos/auditoria_llm_20.csv`, que se genera al ejecutar con el LLM disponible).
- **Parte 3 – funcional en local:** `streamlit run app.py` muestra:
  - filtros, métricas, gráfico, tabla con descarga;
  - el probador en vivo, que usa el modelo entrenado en `modelo/`.

  La métrica de acuerdo LLM-humano aparece como "pendiente". Los pesos (`modelo/model.safetensors`, 516 MB) no se suben a GitHub: para usar la app en otra máquina hay que ejecutar `02_clasificacion.ipynb`, que regenera el modelo.
