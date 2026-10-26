# Tarea 2 – Voces y documentos peruanos: del archivo escaneado al texto buscable

**Pregunta guía:** ¿podemos convertir documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?

| Parte | Estado |
|---|---|
| 1 · Corpus y extracción (OCR + ASR) — `01_extraccion.ipynb` | Lista (pendiente la revisión humana de las transcripciones) |
| 2 · Evaluación y extracción estructurada — `02_evaluacion.ipynb` | Pendiente |
| 3 · Dashboard Streamlit — `app.py` | App lista con los datos de la Parte 1; falta el despliegue en Streamlit Cloud |

## Corpus

- **25 documentos**: 8 impresos nítidos, 8 fotos con sombras o inclinación y 9 manuscritos.
- **21 clips de audio** en español peruano, **42.0 minutos** en total; `clip_011` es una entrevista con tres hablantes (diarización).
- **Fecha de extracción:** 24 y 25 de octubre de 2026.
- Todo archivo tiene URL, autor, licencia, atribución y hash SHA-256 en [`datos/fuentes.csv`](datos/fuentes.csv). Los archivos crudos no se suben al repositorio; se recuperan con `python datos.py`.

### Documentos

| id | tipo | título | autor | licencia |
|---|---|---|---|---|
| doc_001 | impreso | [Mercurio Peruano, tomo V](https://archive.org/details/mercurioperuanod05cale/page/n15) | Sociedad de Amantes del País | Dominio público |
| doc_002 | impreso | [Bases de la Constitución política de la República Peruana](https://archive.org/details/basesdelaconstit00peru/page/n3) | Congreso Constituyente del Perú | Dominio público |
| doc_003 | impreso | [Constitución política de la República Peruana](https://archive.org/details/constitucionpoli00peru/page/n8) | Congreso Constituyente del Perú | Dominio público |
| doc_004 | impreso | [Gaceta del Gobierno (Lima)](https://archive.org/details/gacetadelgobiern00brow/page/n2) | Gobierno del Perú | Dominio público |
| doc_005 | impreso | [Tradiciones peruanas, tomo IV](https://archive.org/details/tradicionesperua04palm/page/n20) | Ricardo Palma | Dominio público |
| doc_006 | impreso | [Aves sin nido](https://archive.org/details/avessinnido00valluoft/page/n20) | Clorinda Matto de Turner | Dominio público |
| doc_007 | impreso | [Carta de agradecimiento del secretario de la Presidencia de la Repú…](https://commons.wikimedia.org/wiki/File:Carta_de_agradecimiento_del_secretario_de_la_Presidencia_de_la_Rep%C3%BAblica_Nazario_Ch%C3%A1vez_Aliaga_al_pintor_Segundo_Ciro_Gallardo_Gallo_en_nombre_del_presidente_Manuel_Prado_Ugarteche.jpg) | Anderson Reyes Trillo | CC0 |
| doc_008 | impreso | [Acta de Creación de los Símbolos para el Distrito de Mache](https://commons.wikimedia.org/wiki/File:Acta_de_Creaci%C3%B3n_de_los_S%C3%ADmbolos_para_el_Distrito_de_Mache.jpg) | Helder Zavaleta Verde | CC BY 4.0 |
| doc_009 | foto | [Acta de la Indepencia del Perù](https://commons.wikimedia.org/wiki/File:Acta_de_la_Indepencia_del_Per%C3%B9.jpg) | Murillo Perú/Murillo Perú | CC BY-SA 3.0 |
| doc_010 | foto | [Carta de Grau a viuda de Prat en monumento chileno](https://commons.wikimedia.org/wiki/File:Carta_de_Grau_a_viuda_de_Prat_en_monumento_chileno.JPG) | Ciberprofe | CC BY-SA 4.0 |
| doc_011 | foto | [Estado General de Miguel Grau](https://commons.wikimedia.org/wiki/File:Estado_General_de_Miguel_Grau.jpg) | Ministerio de Defensa del Perú | CC BY 2.0 |
| doc_012 | foto | [LimaPlacaCatedral1988](https://commons.wikimedia.org/wiki/File:LimaPlacaCatedral1988.JPG) | Miguel Angel Chong | CC BY-SA 3.0 |
| doc_013 | foto | [Placa conmemorativa Mercado Minorista La Parada](https://commons.wikimedia.org/wiki/File:Placa_conmemorativa_Mercado_Minorista_La_Parada.jpg) | El Surquillano | CC0 |
| doc_014 | foto | [Pasaje Acisclo Villarán - Placa conmemorativa](https://commons.wikimedia.org/wiki/File:Pasaje_Acisclo_Villar%C3%A1n_-_Placa_conmemorativa.jpg) | AlejandroFC | CC BY-SA 4.0 |
| doc_015 | foto | [Placa conmemorativa del Teatro Colón en Lima](https://commons.wikimedia.org/wiki/File:Placa_conmemorativa_del_Teatro_Col%C3%B3n_en_Lima.jpg) | AlejandroFC | CC BY-SA 4.0 |
| doc_016 | foto | [Edificio República - Placa](https://commons.wikimedia.org/wiki/File:Edificio_Rep%C3%BAblica_-_Placa.jpg) | AlejandroFC | CC BY-SA 4.0 |
| doc_017 | manuscrito | [Miguel Grau - Brev](https://commons.wikimedia.org/wiki/File:Miguel_Grau_-_Brev.jpg) | Miguel Grau (1834-1879) | Public domain |
| doc_018 | manuscrito | [Acta de Independencia Peru](https://commons.wikimedia.org/wiki/File:Acta_de_Independencia_Peru.jpg) | Manuel Perez de Tudela | Public domain |
| doc_019 | manuscrito | [Asiento de la partida de bautismo de Raúl Porras Barrenechea](https://commons.wikimedia.org/wiki/File:Asiento_de_la_partida_de_bautismo_de_Ra%C3%BAl_Porras_Barrenechea.jpg) | Asiento parroquial de 1897 (reproducido en Pa | Public domain |
| doc_020 | manuscrito | [Joseolaya partida nacimiento chica](https://commons.wikimedia.org/wiki/File:Joseolaya_partida_nacimiento_chica.jpg) | Gabriela lavarello de velaochaga | CC BY-SA 4.0 |
| doc_021 | manuscrito | [Libro de Bautismos en la Gran Villa de Lampa 1655-1722](https://commons.wikimedia.org/wiki/File:Libro_de_Bautismos_en_la_Gran_Villa_de_Lampa_1655-1722.jpg) | Abelchristian111 | CC0 |
| doc_022 | manuscrito | [Libro de Bautismos en la Gran Villa de Lampa 1832](https://commons.wikimedia.org/wiki/File:Libro_de_Bautismos_en_la_Gran_Villa_de_Lampa_1832.jpg) | Abelchristian111 | CC0 |
| doc_023 | manuscrito | [Libro de Bautismos en la Gran Villa de Lampa 1871](https://commons.wikimedia.org/wiki/File:Libro_de_Bautismos_en_la_Gran_Villa_de_Lampa_1871.jpg) | Abelchristian111 | CC0 |
| doc_024 | manuscrito | [Peruvian Telephone Company receipt Lima 1895](https://commons.wikimedia.org/wiki/File:Peruvian_Telephone_Company_receipt_Lima_1895.JPG) | Peruvian Telephone Company | Public domain |
| doc_025 | manuscrito | [Peru revenue stamp on receipt](https://commons.wikimedia.org/wiki/File:Peru_revenue_stamp_on_receipt.jpg) | Goverment of Peru | Public domain |

### Audios

| id | tipo | título | autor | licencia |
|---|---|---|---|---|
| clip_001 | lectura | [Es-Huaca Cruz de Armatambo-article](https://commons.wikimedia.org/wiki/File:Es-Huaca_Cruz_de_Armatambo-article.ogg) | Lucero Novoa Llerena | CC BY-SA 4.0 |
| clip_002 | testimonio | [Testimonio 2 - Salas, pantallas y archivos](https://commons.wikimedia.org/wiki/File:Testimonio_2_-_Salas,_pantallas_y_archivos.ogg) | Renzo Rojas Alvarez | CC BY 4.0 |
| clip_003 | testimonio | [Testimonio 3 - Salas, pantallas y archivos](https://commons.wikimedia.org/wiki/File:Testimonio_3_-_Salas,_pantallas_y_archivos.ogg) | Renzo Rojas Alvarez | CC BY 4.0 |
| clip_004 | testimonio | [Testimonio 6 - Salas, pantallas y archivos](https://commons.wikimedia.org/wiki/File:Testimonio_6_-_Salas,_pantallas_y_archivos.ogg) | Renzo Rojas Alvarez | CC BY 4.0 |
| clip_005 | ~~entrevista_rural~~ (descartado: quechua) | [Manuel Gamarra - Entrevista sobre Marqu, Shansha, Áncash, Perú](https://commons.wikimedia.org/wiki/File:Manuel_Gamarra_-_Entrevista_sobre_Marqu,_Shansha,_%C3%81ncash,_Per%C3%BA.ogg) | Figuemijun | CC BY-SA 4.0 |
| clip_006 | ~~entrevista_rural~~ (descartado: quechua) | [Elena Figueroa - Entrevista sobre Españolada, Shansha, Áncash, Perú](https://commons.wikimedia.org/wiki/File:Elena_Figueroa_-_Entrevista_sobre_Espa%C3%B1olada,_Shansha,_%C3%81ncash,_Per%C3%BA.ogg) | Figuemijun | CC BY-SA 4.0 |
| clip_007 | ~~entrevista_rural~~ (descartado: quechua) | [Maricela Figueroa - Entrevista sobre Kullash (Molle), Shansha, Ánca…](https://commons.wikimedia.org/wiki/File:Maricela_Figueroa_-_Entrevista_sobre_Kullash_(Molle),_Shansha,_%C3%81ncash,_Per%C3%BA.ogg) | Figuemijun | CC BY-SA 4.0 |
| clip_008 | entrevista_calle | [Entrevista en Magdalena por Fiestas Patrias Perú 2022 (1)](https://commons.wikimedia.org/wiki/File:Entrevista_en_Magdalena_por_Fiestas_Patrias_Per%C3%BA_2022_(1).webm) | Rosario MQ | CC BY-SA 4.0 |
| clip_009 | entrevista_calle | [Entrevista en Magdalena por Fiestas Patrias Perú 2022 (2)](https://commons.wikimedia.org/wiki/File:Entrevista_en_Magdalena_por_Fiestas_Patrias_Per%C3%BA_2022_(2).webm) | Rosario MQ | CC BY-SA 4.0 |
| clip_010 | entrevista_calle | [Entrevista en Magdalena por Fiestas Patrias Perú 2022 (3)](https://commons.wikimedia.org/wiki/File:Entrevista_en_Magdalena_por_Fiestas_Patrias_Per%C3%BA_2022_(3).webm) | Rosario MQ | CC BY-SA 4.0 |
| clip_011 | entrevista_multihablante | [Entrevista 2 en la Av. Rivagüero - El Agustino](https://commons.wikimedia.org/wiki/File:Entrevista_2_en_la_Av._Rivag%C3%BCero_-_El_Agustino.ogg) | JorgeFlores-pe | CC BY-SA 4.0 |
| clip_012 | entrevista_calle | [Sanmarquino responde entrevista durante ceremonia por fiestas patrias](https://commons.wikimedia.org/wiki/File:Sanmarquino_responde_entrevista_durante_ceremonia_por_fiestas_patrias.webm) | Ramses iturrizaga | CC BY-SA 4.0 |
| clip_013 | entrevista_calle | [Entrevista 3](https://commons.wikimedia.org/wiki/File:Entrevista_3.wav) | Gianpier Yair Venegas Ambia | CC BY-SA 4.0 |
| clip_014 | entrevista_calle | [Entrevista a ciudadano del Perú](https://commons.wikimedia.org/wiki/File:Entrevista_a_ciudadano_del_Per%C3%BA.ogg) | Javier Fabrizzio Rojas Ayala. | CC BY-SA 4.0 |
| clip_015 | entrevista_calle | [Entrevista realizada en la cuidad de PUCALLPA - Plaza Yarinacocha p…](https://commons.wikimedia.org/wiki/File:Entrevista_realizada_en_la_cuidad_de_PUCALLPA_-_Plaza_Yarinacocha_por_Fiestas_Patrias_2022.mpg) | Andreita Roldans | CC BY-SA 4.0 |
| clip_016 | entrevista_con_musica | [ENTREVISTA A MARIACHIS DE TARMA POR FIESTAS PATRIAS](https://commons.wikimedia.org/wiki/File:ENTREVISTA_A_MARIACHIS_DE_TARMA_POR_FIESTAS_PATRIAS.webm) | Belen Vega | CC BY 3.0 |
| clip_017 | lectura_corpus | [OpenSLR 73 · es_pe_female · pef_02484_00540218480.wav](https://www.openslr.org/73/) | Guevara-Rukoz et al. (2020), Google — Crowdso | CC BY-SA 4.0 |
| clip_018 | lectura_corpus | [OpenSLR 73 · es_pe_female · pef_08784_00523410864.wav](https://www.openslr.org/73/) | Guevara-Rukoz et al. (2020), Google — Crowdso | CC BY-SA 4.0 |
| clip_019 | lectura_corpus | [OpenSLR 73 · es_pe_female · pef_07508_00007411775.wav](https://www.openslr.org/73/) | Guevara-Rukoz et al. (2020), Google — Crowdso | CC BY-SA 4.0 |
| clip_020 | lectura_corpus | [OpenSLR 73 · es_pe_male · pem_07049_01667310146.wav](https://www.openslr.org/73/) | Guevara-Rukoz et al. (2020), Google — Crowdso | CC BY-SA 4.0 |
| clip_021 | lectura_corpus | [OpenSLR 73 · es_pe_male · pem_03034_01170823099.wav](https://www.openslr.org/73/) | Guevara-Rukoz et al. (2020), Google — Crowdso | CC BY-SA 4.0 |
| clip_022 | testimonio | [Testimonio 7 - Salas, pantallas y archivos](https://commons.wikimedia.org/wiki/File:Testimonio_7_-_Salas,_pantallas_y_archivos.ogg) | Renzo Rojas Alvarez | CC BY 4.0 |
| clip_023 | entrevista_calle | [Entrevista 4](https://commons.wikimedia.org/wiki/File:Entrevista_4.wav) | Gianpier Yair Venegas Ambia | CC BY-SA 4.0 |
| clip_024 | entrevista_calle | [Entrevista 1 en la Av. Rivagüero - El Agustino](https://commons.wikimedia.org/wiki/File:Entrevista_1_en_la_Av._Rivag%C3%BCero_-_El_Agustino.ogg) | JorgeFlores-pe | CC BY-SA 4.0 |

### Descartes

Las 23 imágenes del primer intento de corpus se descartaron: no tenían fuente ni licencia verificable (miniaturas de buscador), 14 eran monedas o billetes y había datos personales en un sobre. El detalle por archivo está en la sección 1.1 del notebook.

De los 24 audios descargados, 3 entrevistas de Shansha (Áncash) resultaron estar mayormente en quechua: se descartaron del corpus en español, se reemplazaron por `clip_022` a `clip_024` y quedan en reserva para el caso opcional de quechua de Huaylas (Parte 2). Ningún audio se descartó por falta de voz y no hubo duplicados por hash.

## Seudonimización

Se reemplazan nombres de personas privadas (entrevistados, ciudadanos en documentos recientes), DNI, teléfonos y correos con `voz.seudonimizar`: reglas automáticas más una lista de nombres armada revisando a mano las salidas. Se mantienen figuras públicas e históricas en su papel público. El texto automático original se conserva en `datos/raw/` (no versionado) para la evaluación.

## Dashboard (Parte 3)

**Enlace público:** _pendiente de despliegue en Streamlit Community Cloud_.

La app solo lee los CSV de `datos/` (no instala PaddleOCR, Whisper ni LLM): indicadores, búsqueda en textos OCR y ASR, filtros por tipo de documento, modelo, tipo de grabación, fuente y duración, gráficos Plotly, tablas descargables y exploradores de documentos y audios. Las imágenes se muestran desde sus URLs públicas de Commons/archive.org, salvo las que contienen nombres de personas privadas; los audios se reproducen solo si su transcripción no tuvo que seudonimizarse (las frases de OpenSLR van en `datos/ejemplos/`, CC BY-SA 4.0).

```bash
cd tarea_2
pip install -r requirements.txt
streamlit run app.py
```

## Hallazgos (Parte 1)

1. **El tipo de documento decide la calidad del OCR.** En impresos nítidos PaddleOCR reconoce el texto casi completo (confianza media ≈0,98); en fotos tras vidrio y en manuscritos la confianza cae a 0,4–0,7 y el texto es mayormente ilegible.
2. **El ASR rinde bien en español peruano, pero solo en español.** faster-whisper large-v3-turbo transcribe entrevistas callejeras a unas 120 palabras por minuto y en un tercio del tiempo real; con audio en quechua, forzado a español, inventa frases repetidas: por eso se descartaron 3 clips.

## Limitaciones

1. **Diarización aproximada.** En grabaciones de celular el diarizador separa de más; `n_hablantes` es fiable solo en `clip_011` (fijado en 3 según su ficha) y en el resto es una estimación.
2. **Métricas pendientes.** CER, WER y el acuerdo LLM–humano requieren las transcripciones manuales y la auditoría de la Parte 2; hasta entonces el dashboard muestra «Parte 2» en esos indicadores. Todo se procesó en CPU (Apple M1), lo que limita el tamaño de los modelos.

## Cómo ejecutar la Parte 1

```bash
cd tarea_2
uv venv --python 3.12
uv pip install -r requirements-extraccion.txt
python datos.py                       # descarga imágenes y audios a datos/raw/
# modelos de diarización (sherpa-onnx, licencia MIT/Apache):
mkdir -p modelos/diarizacion && cd modelos/diarizacion
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2
tar xjf sherpa-onnx-pyannote-segmentation-3-0.tar.bz2
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx
cd ../..
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 01_extraccion.ipynb
```

PaddleOCR (~200 MB) y faster-whisper `large-v3-turbo` (~1,6 GB) descargan sus modelos la primera vez. En un Apple M1 sin GPU el OCR tarda unos 40 s por imagen y el ASR procesa a la mitad del tiempo real.

## Estructura

```
tarea_2/
├── 01_extraccion.ipynb         # OCR, ASR, diarización, seudonimización, limpieza y EDA
├── datos.py                    # descarga del corpus desde datos/fuentes.csv
├── voz.py                      # VAD, transcripción, diarización, SRT/TXT, seudonimización
├── requirements-extraccion.txt # versiones exactas del pipeline
├── app.py                      # dashboard Streamlit
├── requirements.txt            # dependencias de la app
├── graficos/                   # gráficos Plotly exportados (HTML)
└── datos/
    ├── documentos.csv          # corpus OCR
    ├── transcripciones.csv     # corpus ASR
    ├── fuentes.csv             # procedencia, licencia y acceso de cada archivo
    ├── ejemplos/               # 5 frases de OpenSLR 73 para reproducir en la app
    └── raw/                    # (no versionado) originales, respaldos crudos, recortes, SRT/TXT
```
