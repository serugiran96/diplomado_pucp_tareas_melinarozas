"""Dashboard Streamlit – Tarea 1: Noticias peruanas, del titular al clasificador.

Ejecutar desde la carpeta tarea_1/:  streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE = Path(__file__).parent
DATOS = BASE / "datos" / "noticias.csv"
MODELO = BASE / "modelo"
METRICAS = MODELO / "metricas.json"
CATEGORIAS = ["politica", "economia", "deportes", "ciencia_tecnologia"]

st.set_page_config(page_title="Clasificador de titulares peruanos", page_icon="🗞️", layout="wide")


@st.cache_data
def cargar_datos():
    return pd.read_csv(DATOS)


@st.cache_data
def cargar_metricas():
    return json.loads(METRICAS.read_text()) if METRICAS.exists() else {}


@st.cache_resource
def cargar_clasificador():
    if not (MODELO / "config.json").exists():
        return None
    from transformers import pipeline
    return pipeline("text-classification", model=str(MODELO), tokenizer=str(MODELO), top_k=None)


df = cargar_datos()
met = cargar_metricas()

st.title("¿Pueden convertir titulares peruanos en un clasificador de noticias?")
st.markdown(
    "Titulares reales de **La República** y **El Comercio** (opción C, comparada), recolectados desde sus RSS y "
    "sitemaps oficiales respetando `robots.txt`, normalizados a 4 categorías (`politica`, `economia`, `deportes`, "
    "`ciencia_tecnologia`), etiquetados también con un LLM como supervisión débil y usados para ajustar un "
    "Transformer ligero (DistilBERT multilingüe). Las métricas del modelo se calculan en un test reservado."
)

st.sidebar.header("Filtros")
medios = st.sidebar.multiselect("Medio", sorted(df.medio.unique()), default=sorted(df.medio.unique()))
cats = st.sidebar.multiselect("Categoría", CATEGORIAS, default=CATEGORIAS)
filtrado = df[df.medio.isin(medios) & df.etiqueta.isin(cats)]

c1, c2, c3 = st.columns(3)
c1.metric("Noticias recolectadas", f"{len(df)}", help=f"{len(filtrado)} con los filtros actuales")
c2.metric("F1 macro en test", f"{met['test_f1_macro']:.2f}" if "test_f1_macro" in met else "pendiente",
          help="Modelo fine-tuned evaluado en el 15% de test reservado")
c3.metric("Acuerdo LLM vs. auditoría humana",
          f"{met['acuerdo_llm_humano'] / met.get('auditoria_n', 20):.0%}" if "acuerdo_llm_humano" in met else "pendiente",
          help="Revisión manual de 20 predicciones al azar")

conteo = filtrado.groupby(["etiqueta", "medio"]).size().reset_index(name="noticias")
fig = px.bar(conteo, x="etiqueta", y="noticias", color="medio", barmode="group", text="noticias",
             category_orders={"etiqueta": CATEGORIAS},
             labels={"etiqueta": "Categoría", "noticias": "Noticias", "medio": "Medio"},
             title="Distribución de categorías (según filtros)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Explorar noticias")
st.dataframe(filtrado, use_container_width=True, hide_index=True,
             column_config={"url": st.column_config.LinkColumn("url")})
st.download_button("Descargar CSV filtrado", filtrado.to_csv(index=False).encode("utf-8"),
                   file_name="noticias_filtradas.csv", mime="text/csv")

st.subheader("Probador en vivo")
titular = st.text_area("Escribe o pega un titular", placeholder="Congreso aprueba nuevo retiro de fondos de AFP")
if st.button("Clasificar"):
    clf = cargar_clasificador()
    if clf is None:
        st.warning("El modelo aún no está en `modelo/`. Ejecuta `02_clasificacion.ipynb` para entrenarlo y guardarlo.")
    elif not titular.strip():
        st.info("Ingresa un titular.")
    else:
        res = clf(titular.strip())
        res = res[0] if isinstance(res[0], list) else res
        scores = sorted(res, key=lambda s: s["score"], reverse=True)
        st.success(f"Categoría predicha: **{scores[0]['label']}** · probabilidad {scores[0]['score']:.1%}")
        st.bar_chart(pd.DataFrame(scores).set_index("label")["score"])
