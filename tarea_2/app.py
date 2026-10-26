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

# Paleta categórica en orden fijo (validada para daltonismo sobre fondo blanco).
AZUL, NARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRIS = "#c3c2b7"
TINTA, TINTA_SECUNDARIA, TINTA_TENUE, REJILLA = "#0b0b0b", "#52514e", "#898781", "#eceae4"

NOMBRE_TIPO_DOC = {"impreso": "Impreso", "foto": "Foto", "manuscrito": "Manuscrito"}
COLOR_TIPO_DOC = {"Impreso": AZUL, "Foto": NARANJA, "Manuscrito": AQUA}
NOMBRE_TIPO_AUDIO = {
    "entrevista_calle": "Entrevista en la calle",
    "entrevista_multihablante": "Entrevista con 3 hablantes",
    "entrevista_con_musica": "Entrevista con música",
    "testimonio": "Testimonio",
    "lectura": "Artículo leído",
    "lectura_corpus": "Frase leída (OpenSLR)",
}
GRUPO_AUDIO = {
    "entrevista_calle": "Entrevista", "entrevista_multihablante": "Entrevista", "entrevista_con_musica": "Entrevista",
    "testimonio": "Testimonio", "lectura": "Lectura", "lectura_corpus": "Lectura",
}
COLOR_GRUPO_AUDIO = {"Entrevista": AZUL, "Testimonio": NARANJA, "Lectura": AQUA}
NOMBRES_MODELOS = {
    "paddle_por_defecto": "PaddleOCR por defecto",
    "paddle_parte1": "PaddleOCR sin desdoblado",
    "easyocr": "EasyOCR",
    "whisper_small": "Whisper small",
    "whisper_large_v3_turbo": "Whisper large-v3-turbo",
    "parakeet_tdt_0.6b_v3": "Parakeet TDT 0.6B",
}
# Cada modelo conserva su color en todos los gráficos; el elegido de cada modalidad va en azul.
COLOR_MODELO = {
    "PaddleOCR sin desdoblado": AZUL, "PaddleOCR por defecto": NARANJA, "EasyOCR": AQUA,
    "Whisper large-v3-turbo": AZUL, "Whisper small": NARANJA, "Parakeet TDT 0.6B": AQUA,
}

st.set_page_config(page_title="Voces y documentos peruanos", page_icon="🎙️", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 2.2rem; max-width: 1240px; }}
      h1 {{ font-size: 2.1rem !important; font-weight: 650; letter-spacing: -0.015em; line-height: 1.2; }}
      h4 {{ font-weight: 600; margin-bottom: 0.1rem; }}
      [data-testid="stMetricLabel"] p {{ color: {TINTA_SECUNDARIA}; font-size: 0.85rem; }}
      [data-testid="stMetricValue"] {{ font-weight: 600; }}
      .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0.4rem 0 1.2rem; }}
      .chip {{ border: 1px solid rgba(11,11,11,0.10); border-radius: 999px; padding: 3px 12px;
               font-size: 0.82rem; color: {TINTA_SECUNDARIA}; background: #fafaf8; }}
      .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
      .stTabs [data-baseweb="tab"] {{ padding: 8px 14px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_datos(version_datos):
    # version_datos cambia cuando se actualiza algún CSV: así la caché no sirve datos viejos.
    documentos = pd.read_csv(CARPETA_DATOS / "documentos.csv", dtype={"texto_referencia": str})
    audios = pd.read_csv(CARPETA_DATOS / "transcripciones.csv", dtype={"texto_referencia": str})
    fuentes = pd.read_csv(CARPETA_DATOS / "fuentes.csv")
    documentos = documentos.merge(fuentes[["id", "url_descarga", "licencia", "autor"]], on="id", how="left")
    audios = audios.merge(fuentes[["id", "url_descarga", "licencia", "autor"]], on="id", how="left")
    for tabla in [documentos, audios]:
        tabla["texto_referencia"] = tabla["texto_referencia"].fillna("")
    documentos["tipo_nombre"] = documentos["tipo"].map(NOMBRE_TIPO_DOC)
    audios["tipo_nombre"] = audios["tipo"].map(NOMBRE_TIPO_AUDIO)
    audios["grupo"] = audios["tipo"].map(GRUPO_AUDIO)
    audios["fuente_simple"] = audios["fuente"].str.split(" (", regex=False).str[0]
    # Resultados de la Parte 2 (si todavía no existen, la app muestra «pendiente»).
    opcionales = {}
    for nombre in ["extraccion_llm", "metricas_modelos", "salidas_modelos", "auditoria_llm"]:
        ruta = CARPETA_DATOS / f"{nombre}.csv"
        opcionales[nombre] = pd.read_csv(ruta, dtype={"correcta": str}) if ruta.exists() else None
    return documentos, audios, opcionales


def estilo(figura, alto=340):
    # Un solo estilo para todos los gráficos: fondo blanco, rejilla tenue, barras con borde redondeado.
    figura.update_layout(
        height=alto,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "system-ui, -apple-system, Segoe UI, sans-serif", "size": 13, "color": TINTA_SECUNDARIA},
        margin={"l": 12, "r": 28, "t": 12, "b": 12},
        barcornerradius=4,
        bargap=0.35,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0, "title_text": ""},
        hoverlabel={"bgcolor": "#ffffff", "bordercolor": "#e1e0d9", "font_color": TINTA},
    )
    # automargin reserva espacio para las etiquetas largas de los ejes (si no, quedan cortadas).
    figura.update_xaxes(gridcolor=REJILLA, linecolor=GRIS, zeroline=False, tickfont_color=TINTA_TENUE, automargin=True)
    figura.update_yaxes(gridcolor=REJILLA, linecolor=GRIS, zeroline=False, tickfont_color=TINTA_TENUE, automargin=True)
    return figura


def mostrar(figura):
    st.plotly_chart(figura, theme=None, width="stretch", config={"displayModeBar": False})


def encabezado_tarjeta(titulo, detalle):
    st.markdown(f"#### {titulo}")
    st.caption(detalle)


def url_vista_previa(fila):
    # Commons entrega una versión reducida con Special:FilePath; archive.org, con _w900.
    if "commons.wikimedia.org" in fila["fuente_url"]:
        nombre = fila["fuente_url"].split("File:")[-1]
        return f"https://commons.wikimedia.org/wiki/Special:FilePath/{nombre}?width=900"
    return fila["url_descarga"].replace("_w1800", "_w900")


version_datos = max(ruta.stat().st_mtime for ruta in CARPETA_DATOS.glob("*.csv"))
documentos, audios, opcionales = cargar_datos(version_datos)
extraccion = opcionales["extraccion_llm"]
metricas = opcionales["metricas_modelos"]
salidas_modelos = opcionales["salidas_modelos"]
auditoria = opcionales["auditoria_llm"]
if metricas is not None:
    metricas["modelo_nombre"] = metricas["modelo"].map(NOMBRES_MODELOS)
if salidas_modelos is not None:
    salidas_modelos["modelo_nombre"] = salidas_modelos["modelo"].map(NOMBRES_MODELOS)

# --- Filtros -----------------------------------------------------------------

st.sidebar.markdown("### Filtros")
busqueda = st.sidebar.text_input("Buscar en los textos (OCR y audio)", placeholder="ej. Perú, cine, constitución")
tipos_documento = st.sidebar.pills("Tipo de documento", list(COLOR_TIPO_DOC), selection_mode="multi",
                                   default=list(COLOR_TIPO_DOC))
tipos_audio = st.sidebar.pills("Tipo de grabación", list(NOMBRE_TIPO_AUDIO.values()), selection_mode="multi",
                               default=list(NOMBRE_TIPO_AUDIO.values()))
opciones_fuente = sorted(audios["fuente_simple"].unique())
fuentes_audio = st.sidebar.pills("Fuente del audio", opciones_fuente, selection_mode="multi", default=opciones_fuente)
duracion_maxima = int(audios["duracion_seg"].max()) + 1
rango_duracion = st.sidebar.slider("Duración del clip (s)", 0, duracion_maxima, (0, duracion_maxima))
modelos_visibles = st.sidebar.pills("Modelos en la evaluación", list(NOMBRES_MODELOS.values()), selection_mode="multi",
                                    default=list(NOMBRES_MODELOS.values()))

docs_filtrados = documentos[documentos["tipo_nombre"].isin(tipos_documento)]
audios_filtrados = audios[
    audios["tipo_nombre"].isin(tipos_audio)
    & audios["fuente_simple"].isin(fuentes_audio)
    & audios["duracion_seg"].between(rango_duracion[0], rango_duracion[1])
]
if busqueda:
    docs_filtrados = docs_filtrados[docs_filtrados["texto_ocr"].str.contains(busqueda, case=False, na=False)]
    audios_filtrados = audios_filtrados[audios_filtrados["texto_asr"].str.contains(busqueda, case=False, na=False)]
    st.sidebar.success(f"«{busqueda}» aparece en {len(docs_filtrados)} documentos y {len(audios_filtrados)} clips")

# --- Encabezado e indicadores --------------------------------------------------

st.title("¿Podemos convertir documentos escaneados y entrevistas en texto buscable?")
st.markdown(
    "Un pipeline de IA lee documentos peruanos con **PaddleOCR** y transcribe entrevistas en español peruano "
    "con **faster-whisper + VAD**, con diarización y seudonimización. Los resultados se calcularon en los "
    "notebooks; aquí se exploran."
)
st.markdown(
    """<div class="chips">
    <span class="chip">25 documentos · impresos, fotos y manuscritos</span>
    <span class="chip">21 clips · 42 minutos</span>
    <span class="chip">Wikimedia Commons</span><span class="chip">archive.org</span><span class="chip">OpenSLR 73</span>
    </div>""",
    unsafe_allow_html=True,
)


def metrica_de(modelo):
    if metricas is None:
        return None
    fila = metricas[metricas["modelo"] == modelo]
    if len(fila) == 0 or pd.isna(fila.iloc[0]["valor"]):
        return None
    return float(fila.iloc[0]["valor"])


cer = metrica_de("paddle_parte1")
wer = metrica_de("whisper_large_v3_turbo")
acuerdo = None
if auditoria is not None:
    revisadas = auditoria[auditoria["correcta"].fillna("").str.strip() != ""]
    if len(revisadas) > 0:
        correctas = revisadas["correcta"].str.strip().str.lower().isin(["sí", "si", "s"]).sum()
        acuerdo = f"{correctas}/{len(revisadas)}"

columnas = st.columns(5)
columnas[0].metric("Documentos procesados", f"{len(docs_filtrados)} de {len(documentos)}", border=True)
columnas[1].metric("Minutos de audio", f"{audios_filtrados['duracion_seg'].sum() / 60:.1f}", border=True)
columnas[2].metric("CER del OCR elegido", f"{cer:.2f}" if cer is not None else "pendiente", border=True,
                   help="Tasa de error por caracteres de PaddleOCR en 10 documentos con transcripción manual. 0 es perfecto.")
columnas[3].metric("WER del ASR elegido", f"{wer:.2f}" if wer is not None else "pendiente", border=True,
                   help="Tasa de error por palabras de Whisper large-v3-turbo en 10 clips con transcripción manual. 0 es perfecto.")
columnas[4].metric("Acuerdo LLM–humano", acuerdo if acuerdo else "pendiente", border=True,
                   help="Extracciones del LLM completamente correctas en la auditoría humana de 20 casos.")

pestana_resumen, pestana_evaluacion, pestana_documentos, pestana_audios = st.tabs(
    ["Resumen", "Evaluación de modelos", "Documentos", "Audios"]
)

# --- Resumen -------------------------------------------------------------------

with pestana_resumen:
    izquierda, derecha = st.columns(2, gap="medium")
    with izquierda:
        with st.container(border=True):
            encabezado_tarjeta("El OCR confía en los impresos; en los manuscritos, mucho menos",
                               "Confianza media que PaddleOCR asigna a lo que reconoce, por tipo de documento")
            if len(docs_filtrados) > 0:
                por_tipo = docs_filtrados.groupby("tipo_nombre").agg(
                    confianza=("confianza_media", "mean"), documentos=("id", "count")).reset_index()
                figura = px.bar(por_tipo, x="confianza", y="tipo_nombre", orientation="h", color="tipo_nombre",
                                color_discrete_map=COLOR_TIPO_DOC, text=por_tipo["confianza"].map("{:.2f}".format),
                                category_orders={"tipo_nombre": list(COLOR_TIPO_DOC)}, range_x=[0, 1.08],
                                custom_data=["documentos"], labels={"confianza": "Confianza media", "tipo_nombre": ""})
                figura.update_traces(textposition="outside",
                                     hovertemplate="%{y}: %{x:.2f}<br>%{customdata[0]} documentos<extra></extra>")
                mostrar(estilo(figura, 260).update_layout(showlegend=False))
            else:
                st.info("Ningún documento cumple los filtros.")
    with derecha:
        with st.container(border=True):
            encabezado_tarjeta("Las entrevistas en la calle aportan la mayor parte del audio",
                               "Minutos de audio por tipo de grabación")
            if len(audios_filtrados) > 0:
                minutos = audios_filtrados.groupby("tipo_nombre")["duracion_seg"].sum().div(60).reset_index()
                minutos = minutos.sort_values("duracion_seg")
                figura = px.bar(minutos, x="duracion_seg", y="tipo_nombre", orientation="h",
                                text=minutos["duracion_seg"].map("{:.1f} min".format),
                                labels={"duracion_seg": "Minutos", "tipo_nombre": ""})
                figura.update_traces(marker_color=AZUL, textposition="outside",
                                     hovertemplate="%{y}: %{x:.1f} min<extra></extra>")
                mostrar(estilo(figura, 260).update_xaxes(range=[0, minutos["duracion_seg"].max() * 1.25]))
            else:
                st.info("Ningún clip cumple los filtros.")

    with st.container(border=True):
        encabezado_tarjeta("A más duración, más palabras: unas 120 por minuto en casi todos los clips",
                           "Cada punto es un clip; los que quedan bajo la nube tienen tramos que el detector de voz descartó")
        if len(audios_filtrados) > 0:
            figura = px.scatter(audios_filtrados, x="duracion_seg", y="palabras", color="grupo",
                                color_discrete_map=COLOR_GRUPO_AUDIO, hover_name="id",
                                category_orders={"grupo": list(COLOR_GRUPO_AUDIO)},
                                custom_data=["tipo_nombre", "n_hablantes"],
                                labels={"duracion_seg": "Duración (s)", "palabras": "Palabras transcritas", "grupo": ""})
            figura.update_traces(marker={"size": 11, "line": {"width": 2, "color": "#ffffff"}},
                                 hovertemplate="<b>%{hovertext}</b> · %{customdata[0]}<br>%{x:.0f} s · %{y} palabras"
                                               " · %{customdata[1]} hablante(s)<extra></extra>")
            mostrar(estilo(figura, 340))

# --- Evaluación de modelos -------------------------------------------------------

with pestana_evaluacion:
    if metricas is None or metricas["valor"].isna().all():
        st.info("La evaluación de modelos estará disponible cuando existan las referencias manuales (Parte 2).")
    else:
        st.markdown("Los seis modelos se midieron sobre **los mismos 10 documentos y 10 clips**, contra transcripciones "
                    "manuales. Barras más cortas = menos errores; en azul, el modelo elegido.")
        izquierda, derecha = st.columns(2, gap="medium")
        for columna, modalidad, metrica, titulo in [
            (izquierda, "documento", "CER", "OCR: sin desdoblado de página, PaddleOCR comete la mitad de errores"),
            (derecha, "audio", "WER", "Audio: Whisper large-v3-turbo es el más preciso"),
        ]:
            with columna, st.container(border=True):
                encabezado_tarjeta(titulo, f"{metrica} medio por modelo · costo en CPU (Apple M1) en la etiqueta emergente")
                tabla = metricas[(metricas["modalidad"] == modalidad) & metricas["modelo_nombre"].isin(modelos_visibles)]
                if len(tabla) == 0:
                    st.info("Elige al menos un modelo en los filtros.")
                    continue
                tabla = tabla.sort_values("valor", ascending=False)
                figura = px.bar(tabla, x="valor", y="modelo_nombre", orientation="h", color="modelo_nombre",
                                color_discrete_map=COLOR_MODELO, text=tabla["valor"].map("{:.2f}".format),
                                custom_data=["costo"], labels={"valor": metrica, "modelo_nombre": ""})
                figura.update_traces(textposition="outside",
                                     hovertemplate="%{y}<br>" + metrica + " %{x:.2f}<br>%{customdata[0]}<extra></extra>")
                mostrar(estilo(figura, 230).update_layout(showlegend=False).update_xaxes(range=[0, tabla["valor"].max() * 1.3]))

        if salidas_modelos is not None and salidas_modelos["valor"].notna().any():
            visibles = salidas_modelos[salidas_modelos["modelo_nombre"].isin(modelos_visibles) & salidas_modelos["valor"].notna()]
            tipo_por_id = {**documentos.set_index("id")["tipo_nombre"].to_dict(), **audios.set_index("id")["grupo"].to_dict()}
            visibles = visibles.assign(categoria=visibles["id"].map(tipo_por_id))
            izquierda, derecha = st.columns(2, gap="medium")
            for columna, modalidad, metrica, titulo, orden in [
                (izquierda, "documento", "CER", "Los manuscritos concentran los errores de todos los OCR", list(COLOR_TIPO_DOC)),
                (derecha, "audio", "WER", "Las entrevistas son el caso difícil del audio", list(COLOR_GRUPO_AUDIO)),
            ]:
                with columna, st.container(border=True):
                    encabezado_tarjeta(titulo, f"{metrica} medio por tipo y modelo")
                    tabla = visibles[visibles["modalidad"] == modalidad]
                    if len(tabla) == 0:
                        st.info("Elige al menos un modelo en los filtros.")
                        continue
                    tabla = tabla.groupby(["categoria", "modelo_nombre"])["valor"].mean().reset_index()
                    modelos = [m for m in NOMBRES_MODELOS.values() if m in set(tabla["modelo_nombre"])]
                    figura = px.bar(tabla, x="categoria", y="valor", color="modelo_nombre", barmode="group",
                                    category_orders={"categoria": orden, "modelo_nombre": modelos},
                                    color_discrete_map=COLOR_MODELO,
                                    labels={"valor": metrica, "categoria": "", "modelo_nombre": ""})
                    figura.update_traces(hovertemplate="%{x} · %{fullData.name}<br>" + metrica + " %{y:.2f}<extra></extra>")
                    mostrar(estilo(figura, 300).update_layout(bargap=0.25, bargroupgap=0.08))

        with st.container(border=True):
            encabezado_tarjeta("Extracción estructurada con LLM",
                               "Qwen2.5-0.5B-Instruct local extrajo tema, resumen y campos de cada texto; una persona auditó 20 casos")
            if auditoria is not None and acuerdo:
                st.markdown(f"**{acuerdo} extracciones completamente correctas.** El modelo sigue el formato JSON pero "
                            "inventa hechos cuando el OCR es ilegible y deja en `null` fechas y emisores que sí aparecen.")
                st.dataframe(auditoria[["id", "modalidad", "correcta", "error_observado"]], hide_index=True, width="stretch",
                             column_config={"error_observado": st.column_config.TextColumn("Error observado", width="large"),
                                            "correcta": "¿Correcta?"})

# --- Explorador de documentos ------------------------------------------------------

with pestana_documentos:
    with st.container(border=True):
        encabezado_tarjeta("Documentos procesados", "Texto OCR automático y seudonimizado; usa los filtros de la izquierda")
        columnas_tabla = ["id", "tipo_nombre", "titulo", "fuente", "confianza_media", "n_caracteres", "texto_ocr"]
        st.dataframe(docs_filtrados[columnas_tabla], hide_index=True, width="stretch", height=280, column_config={
            "tipo_nombre": "Tipo", "titulo": "Título", "fuente": "Fuente", "texto_ocr": "Texto OCR",
            "n_caracteres": st.column_config.NumberColumn("Caracteres"),
            "confianza_media": st.column_config.ProgressColumn("Confianza OCR", min_value=0, max_value=1, format="%.2f"),
        })
        st.download_button("Descargar CSV", docs_filtrados[columnas_tabla].to_csv(index=False).encode("utf-8"),
                           "documentos_filtrados.csv", "text/csv")

    if len(docs_filtrados) == 0:
        st.info("Ningún documento cumple los filtros.")
    else:
        opciones = {f"{f.id} · {f.tipo_nombre} · {f.titulo[:70]}": f.id for f in docs_filtrados.itertuples()}
        elegido = st.selectbox("Elige un documento", list(opciones))
        fila = docs_filtrados[docs_filtrados["id"] == opciones[elegido]].iloc[0]

        texto_col, imagen_col = st.columns([3, 2], gap="medium")
        with texto_col, st.container(border=True):
            st.markdown(f"#### {fila['titulo']}")
            st.caption(f"{fila['tipo_nombre']} · {fila['autor']} · {fila['licencia']} · "
                       f"confianza OCR {fila['confianza_media']:.2f} · {fila['n_caracteres']} caracteres")
            st.markdown(f"[Ver fuente original]({fila['fuente_url']})")
            st.text_area("Texto OCR (automático, seudonimizado)", fila["texto_ocr"], height=300)
            if fila["texto_referencia"]:
                st.text_area("Transcripción manual de referencia", fila["texto_referencia"], height=180)
                if salidas_modelos is not None:
                    comparacion = salidas_modelos[salidas_modelos["id"] == fila["id"]][["modelo_nombre", "valor"]]
                    st.dataframe(comparacion, hide_index=True, column_config={
                        "modelo_nombre": "Modelo", "valor": st.column_config.NumberColumn("CER", format="%.2f")})
            else:
                st.caption("Este documento no forma parte de la muestra de evaluación (10 documentos con transcripción manual).")
            st.markdown("**Campos extraídos por el LLM**")
            if extraccion is not None and fila["id"] in set(extraccion["id"]):
                st.json(json.loads(extraccion[extraccion["id"] == fila["id"]].iloc[0]["campos_json"]), expanded=True)
            else:
                st.caption("Sin extracción del LLM para este documento.")
        with imagen_col, st.container(border=True):
            if fila["id"] in DOCUMENTOS_SIN_VISTA:
                st.info("Vista previa no disponible: la imagen muestra nombres de personas privadas.")
            else:
                # Copia liviana incluida en el repositorio (licencia libre); si falta, se usa la URL pública.
                vista_local = CARPETA_DATOS / "ejemplos" / f"{fila['id']}.jpg"
                imagen = str(vista_local) if vista_local.exists() else url_vista_previa(fila)
                st.image(imagen, caption=f"{fila['licencia']} · {fila['autor']}", width="stretch")

# --- Explorador de audios -----------------------------------------------------------

with pestana_audios:
    with st.container(border=True):
        encabezado_tarjeta("Clips transcritos", "Transcripción automática y seudonimizada; usa los filtros de la izquierda")
        columnas_tabla = ["id", "tipo_nombre", "duracion_seg", "n_hablantes", "palabras", "fuente", "texto_asr"]
        st.dataframe(audios_filtrados[columnas_tabla], hide_index=True, width="stretch", height=280, column_config={
            "tipo_nombre": "Tipo", "fuente": "Fuente", "texto_asr": "Transcripción", "palabras": "Palabras",
            "n_hablantes": "Hablantes", "duracion_seg": st.column_config.NumberColumn("Duración", format="%.0f s"),
        })
        st.download_button("Descargar CSV", audios_filtrados[columnas_tabla].to_csv(index=False).encode("utf-8"),
                           "transcripciones_filtradas.csv", "text/csv")

    if len(audios_filtrados) == 0:
        st.info("Ningún clip cumple los filtros.")
    else:
        opciones = {f"{f.id} · {f.tipo_nombre} · {f.duracion_seg:.0f} s": f.id for f in audios_filtrados.itertuples()}
        elegido = st.selectbox("Elige un clip", list(opciones))
        fila = audios_filtrados[audios_filtrados["id"] == opciones[elegido]].iloc[0]

        with st.container(border=True):
            st.markdown(f"#### {fila['id']} · {fila['tipo_nombre']}")
            st.caption(f"{fila['duracion_seg']:.0f} s · {fila['n_hablantes']} hablante(s) · diarización: {fila['diarizacion']} · "
                       f"{fila['autor']} · {fila['licencia']}")
            st.markdown(f"[Ver fuente original]({fila['fuente_url']})")
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
            st.text_area("Transcripción (Whisper large-v3-turbo, seudonimizada)", texto, height=300)
            if fila["texto_referencia"]:
                st.text_area("Transcripción manual de referencia", fila["texto_referencia"], height=180)
            if salidas_modelos is not None and fila["id"] in set(salidas_modelos["id"]):
                st.markdown("**Comparación de modelos en este clip**")
                for salida in salidas_modelos[salidas_modelos["id"] == fila["id"]].itertuples():
                    etiqueta = salida.modelo_nombre
                    if pd.notna(salida.valor):
                        etiqueta += f" · WER {salida.valor:.2f}"
                    st.text_area(etiqueta, salida.texto, height=110)
            else:
                st.caption("Este clip no forma parte de la muestra de evaluación: se muestra solo la transcripción del modelo elegido.")
