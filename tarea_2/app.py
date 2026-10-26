"""Dashboard de la Tarea 2: voces y documentos peruanos convertidos en texto buscable.

Solo lee los CSV que generaron los notebooks: no ejecuta OCR, ASR ni LLM en vivo.
Ejecutar en local:  streamlit run app.py
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

CARPETA = Path(__file__).parent
CARPETA_DATOS = CARPETA / "datos"

# Documentos cuya imagen contiene nombres de personas privadas: se consultan
# solo como texto seudonimizado, sin vista previa.
DOCUMENTOS_SIN_VISTA = ["doc_007", "doc_008", "doc_019"]

st.set_page_config(page_title="Voces y documentos peruanos", page_icon="🎙️", layout="wide")


@st.cache_data
def cargar_datos():
    # texto_referencia se lee como texto aunque esté vacía (se llena en la Parte 2).
    documentos = pd.read_csv(CARPETA_DATOS / "documentos.csv", dtype={"texto_referencia": str})
    audios = pd.read_csv(CARPETA_DATOS / "transcripciones.csv", dtype={"texto_referencia": str})
    fuentes = pd.read_csv(CARPETA_DATOS / "fuentes.csv")
    documentos = documentos.merge(fuentes[["id", "url_descarga", "licencia", "autor"]], on="id", how="left")
    audios = audios.merge(fuentes[["id", "url_descarga", "licencia", "autor"]], on="id", how="left")
    for tabla in [documentos, audios]:
        tabla["texto_referencia"] = tabla["texto_referencia"].fillna("")
    extraccion = None
    if (CARPETA_DATOS / "extraccion_llm.csv").exists():
        extraccion = pd.read_csv(CARPETA_DATOS / "extraccion_llm.csv")
    return documentos, audios, extraccion


def distancia_edicion(a, b):
    # Levenshtein por filas: suficiente para textos de pocas páginas.
    anterior = list(range(len(b) + 1))
    for i, letra_a in enumerate(a, start=1):
        actual = [i]
        for j, letra_b in enumerate(b, start=1):
            actual.append(min(anterior[j] + 1, actual[j - 1] + 1, anterior[j - 1] + (letra_a != letra_b)))
        anterior = actual
    return anterior[-1]


def tasa_error(automatico, referencia, por_palabras):
    if por_palabras:
        automatico = automatico.replace("[HABLANTE_", " [HABLANTE_").split()
        automatico = [palabra for palabra in automatico if not palabra.startswith("[HABLANTE_")]
        referencia = referencia.split()
    if len(referencia) == 0:
        return None
    return distancia_edicion(automatico, referencia) / len(referencia)


def url_vista_previa(fila):
    # Commons entrega una versión reducida con Special:FilePath; archive.org, con _w900.
    if "commons.wikimedia.org" in fila["fuente_url"]:
        nombre = fila["fuente_url"].split("File:")[-1]
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{nombre}?width=900"
    return fila["url_descarga"].replace("_w1800", "_w900")


documentos, audios, extraccion = cargar_datos()

# --- Encabezado --------------------------------------------------------------

st.title("¿Podemos convertir documentos escaneados y entrevistas en un archivo de texto buscable?")
st.markdown(
    "Pipeline de IA sobre un corpus peruano con licencia abierta: **25 documentos** (impresos, fotos con "
    "sombras o inclinación y manuscritos) leídos con **PaddleOCR**, y **21 clips de audio** en español "
    "peruano transcritos con **faster-whisper + VAD**, con diarización y seudonimización. "
    "Fuentes: Wikimedia Commons, archive.org y OpenSLR 73. Los resultados se calcularon en los notebooks; "
    "esta app solo los explora."
)

# --- Filtros -----------------------------------------------------------------

st.sidebar.header("Filtros")
busqueda = st.sidebar.text_input("Buscar palabra en OCR y ASR", placeholder="ej. Perú, cine, constitución")
tipos_documento = st.sidebar.multiselect("Tipo de documento", ["impreso", "foto", "manuscrito"],
                                         default=["impreso", "foto", "manuscrito"])
modelos_ocr = st.sidebar.multiselect("Modelo OCR", sorted(documentos["modelo_ocr"].unique()),
                                     default=sorted(documentos["modelo_ocr"].unique()))
tipos_audio = st.sidebar.multiselect("Tipo de grabación", sorted(audios["tipo"].unique()),
                                     default=sorted(audios["tipo"].unique()))
fuentes_audio = st.sidebar.multiselect("Fuente del audio", sorted(audios["fuente"].unique()),
                                       default=sorted(audios["fuente"].unique()))
duracion_maxima = int(audios["duracion_seg"].max()) + 1
rango_duracion = st.sidebar.slider("Duración del clip (s)", 0, duracion_maxima, (0, duracion_maxima))

docs_filtrados = documentos[documentos["tipo"].isin(tipos_documento) & documentos["modelo_ocr"].isin(modelos_ocr)]
audios_filtrados = audios[
    audios["tipo"].isin(tipos_audio)
    & audios["fuente"].isin(fuentes_audio)
    & audios["duracion_seg"].between(rango_duracion[0], rango_duracion[1])
]
if busqueda:
    docs_filtrados = docs_filtrados[docs_filtrados["texto_ocr"].str.contains(busqueda, case=False, na=False)]
    audios_filtrados = audios_filtrados[audios_filtrados["texto_asr"].str.contains(busqueda, case=False, na=False)]
    st.sidebar.success(f"«{busqueda}» aparece en {len(docs_filtrados)} documentos y {len(audios_filtrados)} clips")

# --- Indicadores ---------------------------------------------------------------

con_referencia_docs = documentos[documentos["texto_referencia"] != ""]
con_referencia_audios = audios[audios["texto_referencia"] != ""]
cer = None
if len(con_referencia_docs) > 0:
    errores = [tasa_error(f.texto_ocr, f.texto_referencia, False) for f in con_referencia_docs.itertuples()]
    cer = sum(errores) / len(errores)
wer = None
if len(con_referencia_audios) > 0:
    errores = [tasa_error(f.texto_asr, f.texto_referencia, True) for f in con_referencia_audios.itertuples()]
    wer = sum(errores) / len(errores)

columnas = st.columns(5)
columnas[0].metric("Documentos procesados", f"{len(docs_filtrados)} / {len(documentos)}")
columnas[1].metric("Minutos de audio transcritos", f"{audios_filtrados['duracion_seg'].sum() / 60:.1f}")
columnas[2].metric(f"CER OCR ({len(con_referencia_docs)} docs)", f"{cer:.2f}" if cer is not None else "Parte 2")
columnas[3].metric(f"WER ASR ({len(con_referencia_audios)} clips)", f"{wer:.2f}" if wer is not None else "Parte 2")
columnas[4].metric("Acuerdo LLM–auditoría humana", "Parte 2")
if cer is None or wer is None:
    st.caption("CER, WER y acuerdo LLM–humano se completan con las referencias manuales y la auditoría de la Parte 2.")

pestana_resultados, pestana_documentos, pestana_audios = st.tabs(["📊 Resultados", "📄 Documentos", "🎙️ Audios"])

# --- Resultados ------------------------------------------------------------------

with pestana_resultados:
    izquierda, derecha = st.columns(2)
    if len(docs_filtrados) > 0:
        por_tipo = docs_filtrados.groupby("tipo").agg(
            documentos=("id", "count"), confianza=("confianza_media", "mean"), caracteres=("n_caracteres", "median")
        ).reset_index()
        figura = px.bar(por_tipo, x="tipo", y="confianza", color="tipo", text=por_tipo["confianza"].round(2),
                        hover_data=["documentos", "caracteres"], range_y=[0, 1],
                        category_orders={"tipo": ["impreso", "foto", "manuscrito"]},
                        labels={"tipo": "Tipo", "confianza": "Confianza media del OCR"},
                        title="El OCR confía casi por completo en los impresos y mucho menos en manuscritos")
        figura.update_layout(showlegend=False)
        izquierda.plotly_chart(figura, width="stretch")
    if len(audios_filtrados) > 0:
        figura = px.bar(audios_filtrados.sort_values("duracion_seg", ascending=False), x="id", y="duracion_seg",
                        color="tipo", hover_data=["palabras", "n_hablantes"],
                        labels={"id": "Clip", "duracion_seg": "Duración (s)", "tipo": "Tipo"},
                        title="Las entrevistas en la calle concentran la mayor parte del audio")
        derecha.plotly_chart(figura, width="stretch")
    if len(audios_filtrados) > 0:
        figura = px.scatter(audios_filtrados, x="duracion_seg", y="palabras", color="tipo", hover_name="id",
                            labels={"duracion_seg": "Duración (s)", "palabras": "Palabras transcritas", "tipo": "Tipo"},
                            title="A más duración, más palabras: unas 120 por minuto en casi todos los clips")
        st.plotly_chart(figura, width="stretch")

# --- Explorador de documentos ------------------------------------------------------

with pestana_documentos:
    st.subheader("Tabla de documentos (texto OCR seudonimizado)")
    columnas_tabla = ["id", "tipo", "titulo", "fuente", "confianza_media", "n_caracteres", "texto_ocr"]
    st.dataframe(docs_filtrados[columnas_tabla], width="stretch", hide_index=True)
    st.download_button("Descargar CSV", docs_filtrados[columnas_tabla].to_csv(index=False).encode("utf-8"),
                       "documentos_filtrados.csv", "text/csv")

    if len(docs_filtrados) == 0:
        st.info("Ningún documento cumple los filtros.")
    else:
        opciones = {f"{f.id} · {f.tipo} · {f.titulo[:70]}": f.id for f in docs_filtrados.itertuples()}
        elegido = st.selectbox("Elige un documento", list(opciones))
        fila = docs_filtrados[docs_filtrados["id"] == opciones[elegido]].iloc[0]

        texto_col, imagen_col = st.columns([3, 2])
        with texto_col:
            st.markdown(f"**{fila['titulo']}**  \n{fila['autor']} · {fila['licencia']} · [ver fuente]({fila['fuente_url']})")
            st.markdown(f"Confianza media del OCR: **{fila['confianza_media']:.2f}** · {fila['n_caracteres']} caracteres")
            st.text_area("Texto OCR (automático, seudonimizado)", fila["texto_ocr"], height=320)
            if fila["texto_referencia"]:
                st.text_area("Texto de referencia (manual)", fila["texto_referencia"], height=200)
                st.metric("CER de este documento", f"{tasa_error(fila['texto_ocr'], fila['texto_referencia'], False):.2f}")
            else:
                st.caption("Sin transcripción manual de referencia: se completa en la Parte 2 para la muestra de evaluación.")
            st.markdown("**Campos estructurados (LLM)**")
            if extraccion is not None and fila["id"] in set(extraccion["id"]):
                st.json(json.loads(extraccion[extraccion["id"] == fila["id"]].iloc[0]["campos_json"]))
            else:
                st.caption("La extracción con LLM se agrega en la Parte 2.")
        with imagen_col:
            if fila["id"] in DOCUMENTOS_SIN_VISTA:
                st.info("Vista previa no disponible: la imagen muestra nombres de personas privadas.")
            else:
                st.image(url_vista_previa(fila), caption=f"{fila['licencia']} · {fila['autor']}")

# --- Explorador de audios -----------------------------------------------------------

with pestana_audios:
    st.subheader("Tabla de clips (transcripción seudonimizada)")
    columnas_tabla = ["id", "tipo", "duracion_seg", "n_hablantes", "palabras", "fuente", "texto_asr"]
    st.dataframe(audios_filtrados[columnas_tabla], width="stretch", hide_index=True)
    st.download_button("Descargar CSV", audios_filtrados[columnas_tabla].to_csv(index=False).encode("utf-8"),
                       "transcripciones_filtradas.csv", "text/csv")

    if len(audios_filtrados) == 0:
        st.info("Ningún clip cumple los filtros.")
    else:
        opciones = {f"{f.id} · {f.tipo} · {f.duracion_seg:.0f} s": f.id for f in audios_filtrados.itertuples()}
        elegido = st.selectbox("Elige un clip", list(opciones))
        fila = audios_filtrados[audios_filtrados["id"] == opciones[elegido]].iloc[0]

        st.markdown(f"{fila['autor']} · {fila['licencia']} · [ver fuente]({fila['fuente_url']})  \n"
                    f"**{fila['n_hablantes']} hablante(s)** · diarización: {fila['diarizacion']}")
        # Si el texto tuvo que seudonimizarse, el audio contiene nombres reales: no se reproduce.
        tiene_datos_personales = "[PERSONA_" in fila["texto_asr"] or "[NOMBRE]" in fila["texto_asr"]
        ejemplo_local = CARPETA_DATOS / "ejemplos" / f"{fila['id']}.wav"
        if tiene_datos_personales:
            st.info("Reproducción no disponible: en el audio se mencionan nombres de personas. Se consulta solo el texto.")
        elif ejemplo_local.exists():
            st.audio(str(ejemplo_local))
        else:
            st.audio(fila["url_descarga"])

        texto = fila["texto_asr"].replace(" [HABLANTE_", "\n\n[HABLANTE_")
        st.text_area("Transcripción ASR (automática, seudonimizada)", texto, height=320)
        if fila["texto_referencia"]:
            st.text_area("Texto de referencia (manual)", fila["texto_referencia"], height=200)
            st.metric("WER de este clip", f"{tasa_error(fila['texto_asr'], fila['texto_referencia'], True):.2f}")
        else:
            st.caption("Sin referencia manual ni segundo modelo todavía: la comparación de WER entre modelos llega en la Parte 2.")
