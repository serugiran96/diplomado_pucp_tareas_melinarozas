# Tarea 2 – Voces y documentos peruanos: del archivo escaneado al texto buscable

**Pregunta guía:** ¿podemos convertir documentos escaneados y entrevistas en audio en un archivo de texto estructurado y buscable?

| Parte | Estado |
|---|---|
| 1 · Corpus y extracción (OCR + ASR) — `01_extraccion.ipynb` | Lista (pendiente la revisión humana de las transcripciones) |
| 2 · Evaluación y extracción estructurada — `02_evaluacion.ipynb` | Completa |
| 3 · Dashboard Streamlit — `app.py` | Desplegado: https://voces-documentos-peruanos-mr.streamlit.app/ (CER/WER y LLM se suman con la Parte 2) |

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

**Enlace público:** https://voces-documentos-peruanos-mr.streamlit.app/

La app solo lee los CSV de `datos/` (no instala PaddleOCR, Whisper ni LLM): indicadores, búsqueda en textos OCR y ASR, filtros por tipo de documento, modelo, tipo de grabación, fuente y duración, gráficos Plotly, tablas descargables y exploradores de documentos y audios. Las vistas previas de documentos son copias livianas (900 px) de imágenes con licencia libre en `datos/ejemplos/`, salvo las 3 que contienen nombres de personas privadas; los audios se reproducen solo si su transcripción no tuvo que seudonimizarse (las frases de OpenSLR también van en `datos/ejemplos/`, CC BY-SA 4.0). El tema claro está fijado en `.streamlit/config.toml`.

```bash
cd tarea_2
pip install -r requirements.txt
streamlit run app.py
```

## Evaluación (Parte 2)

Muestra fija de 10 documentos (3 impresos, 4 fotos, 3 manuscritos) y 10 clips (lecturas, testimonios, entrevistas en la calle y una con música), con transcripciones manuales de referencia. Todos los modelos con su configuración por defecto, sin ajustes mirando los resultados.

| Modalidad | Modelo | Error | Costo en CPU (Apple M1) |
|---|---|---|---|
| Documentos | PaddleOCR por defecto (línea base) | CER 0,29 | 19 s por imagen |
| Documentos | **PaddleOCR sin desdoblado ni orientación (Parte 1)** | **CER 0,16** | 15 s por imagen |
| Documentos | EasyOCR 1.7 (alternativo) | CER 0,30 | 33 s por imagen |
| Audio | faster-whisper small (línea base) | WER 0,23 | factor de tiempo real 0,25 |
| Audio | **faster-whisper large-v3-turbo** | **WER 0,13** | factor de tiempo real 0,25 |
| Audio | Parakeet TDT 0.6B v3 vía sherpa-onnx (alternativo) | WER 0,21 | factor de tiempo real 0,09 |

**Elección:** PaddleOCR con la configuración de la Parte 1 y faster-whisper large-v3-turbo; Parakeet si la latencia importa más que la precisión. Para manuscritos ningún modelo sirve (CER 0,28–0,67). La extracción estructurada usa Qwen2.5-0.5B-Instruct local (`datos/extraccion_llm.csv`, JSON válido en 44 de 46 textos); en la auditoría humana (`datos/auditoria_llm.csv`) solo **2 de 20 extracciones fueron completamente correctas (10 %)**: inventa hechos cuando el OCR es ilegible y deja en `null` fechas y emisores que sí aparecen.

**Resultados finales:** WER 0,13 · CER 0,16 · Acuerdo LLM–humano 2/20.

## Hallazgos

1. **La configuración del OCR pesa tanto como el modelo.** PaddleOCR por defecto activa el desdoblado de página y la corrección de orientación, que deforman las fotos de placas (CER 0,74–0,77 en dos de ellas); sin esos módulos el CER medio baja de 0,29 a 0,16. En impresos nítidos el OCR es casi perfecto y en manuscritos ninguno sirve.
2. **En audio el cuello de botella fue la detección de voz, no el reconocedor.** large-v3-turbo transcribe testimonios, entrevistas y hasta un clip con música con WER de 0,02 a 0,12; el peor caso (WER ≈0,8 en todos los modelos) es una entrevista donde el VAD solo marcó 28 de 90 s como voz porque la entrevistada habla bajo y lejos del micrófono. Con audio en quechua, Whisper forzado a español inventa frases: por eso se descartaron 3 clips.

## Limitaciones

1. **Diarización y detección de voz aproximadas.** `n_hablantes` es fiable solo en `clip_011` (fijado en 3 según su ficha); en el resto es una estimación. El VAD descarta voces bajas o lejanas, lo que deja frases sin transcribir en entrevistas grabadas con celular.
2. **Modelos chicos por el hardware.** Todo corrió en CPU con 8 GB de RAM: el LLM es de solo 0,5 mil millones de parámetros (inventa datos en algunos resúmenes) y no se probó MMS para el quechua por su tamaño.

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
├── 02_evaluacion.ipynb         # CER/WER, 3 OCR, 3 ASR, extracción con LLM y auditoría
├── datos.py                    # descarga del corpus desde datos/fuentes.csv
├── voz.py                      # VAD, transcripción, diarización, SRT/TXT, seudonimización
├── requirements-extraccion.txt # versiones exactas del pipeline
├── app.py                      # dashboard Streamlit (tema en .streamlit/config.toml)
├── modelos/README.md           # modelos usados, configuración y cómo descargarlos
├── requirements.txt            # dependencias de la app
├── graficos/                   # gráficos Plotly exportados (HTML)
└── datos/
    ├── documentos.csv          # corpus OCR
    ├── transcripciones.csv     # corpus ASR
    ├── fuentes.csv             # procedencia, licencia y acceso de cada archivo
    ├── extraccion_llm.csv      # campos JSON extraídos por Qwen2.5-0.5B
    ├── auditoria_llm.csv       # revisión humana de 20 extracciones
    ├── metricas_modelos.csv    # CER/WER y costo de cada modelo
    ├── salidas_modelos.csv     # texto de cada modelo en la muestra de evaluación
    ├── referencias/LEEME.md    # reglas de las transcripciones manuales
    ├── ejemplos/               # vistas previas de 22 documentos y 5 frases de OpenSLR 73 (licencias libres)
    └── raw/                    # (no versionado) originales, respaldos crudos, recortes, SRT/TXT
```
