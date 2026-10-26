"""Herramientas de audio para la Tarea 2 (equivalente al voz.py de la Sesión 13).

Pasos que cubre:
1. convertir_a_wav      -> cualquier audio/video a WAV 16 kHz mono
2. detectar_voz         -> segundos con voz según el VAD Silero (descarta clips sin voz)
3. transcribir          -> faster-whisper con VAD activado
4. diarizar             -> quién habla cuándo (pyannote-segmentation 3.0 + WeSpeaker, vía sherpa-onnx)
5. asignar_hablantes    -> une cada frase de Whisper con su hablante
6. a_srt / a_txt        -> exportación de subtítulos y texto plano
7. seudonimizar         -> reemplaza nombres, DNI, teléfonos y correos por etiquetas
"""

import re
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf

FRECUENCIA = 16000
CARPETA_MODELOS = Path(__file__).parent / "modelos" / "diarizacion"


def convertir_a_wav(entrada, salida):
    # Whisper y el diarizador trabajan a 16 kHz y un solo canal; convertir
    # una vez evita que cada modelo remuestree por su cuenta.
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    comando = [ffmpeg, "-y", "-loglevel", "error", "-i", str(entrada),
               "-vn", "-ac", "1", "-ar", str(FRECUENCIA), str(salida)]
    subprocess.run(comando, check=True)


def duracion_segundos(ruta_wav):
    info = sf.info(str(ruta_wav))
    return info.frames / info.samplerate


def detectar_voz(ruta_wav):
    from faster_whisper.audio import decode_audio
    from faster_whisper.vad import VadOptions, get_speech_timestamps

    audio = decode_audio(str(ruta_wav), sampling_rate=FRECUENCIA)
    tramos = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=500))
    muestras_con_voz = 0
    for tramo in tramos:
        muestras_con_voz += tramo["end"] - tramo["start"]
    return muestras_con_voz / FRECUENCIA


def transcribir(modelo, ruta_wav):
    # vad_filter recorta silencios y música antes de decodificar: es la defensa
    # principal contra las frases inventadas de Whisper en tramos sin voz.
    # condition_on_previous_text=False evita que un error se repita en bucle.
    segmentos, info = modelo.transcribe(
        str(ruta_wav),
        language="es",
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
    )
    frases = []
    for segmento in segmentos:
        frases.append({"inicio": segmento.start, "fin": segmento.end, "texto": segmento.text.strip()})
    return frases, info


def crear_diarizador(umbral=0.7, n_hablantes=-1):
    # La huella de voz es ERes2Net (3D-Speaker): en la entrevista de prueba separó
    # entrevistador y entrevistadas mejor que WeSpeaker y TitaNet.
    import sherpa_onnx

    configuracion = sherpa_onnx.OfflineSpeakerDiarizationConfig(
        segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
            pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                model=str(CARPETA_MODELOS / "sherpa-onnx-pyannote-segmentation-3-0" / "model.onnx")
            ),
            num_threads=4,
        ),
        embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=str(CARPETA_MODELOS / "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"),
            num_threads=4,
        ),
        # n_hablantes=-1: el número de hablantes no se fija, lo decide el umbral
        # de distancia entre huellas de voz (más bajo = separa más hablantes).
        clustering=sherpa_onnx.FastClusteringConfig(num_clusters=n_hablantes, threshold=umbral),
        min_duration_on=0.3,
        min_duration_off=0.5,
    )
    return sherpa_onnx.OfflineSpeakerDiarization(configuracion)


def diarizar(diarizador, ruta_wav):
    audio, frecuencia = sf.read(str(ruta_wav), dtype="float32")
    if frecuencia != diarizador.sample_rate:
        raise ValueError(f"Se esperaba {diarizador.sample_rate} Hz y el archivo tiene {frecuencia} Hz")
    resultado = diarizador.process(audio).sort_by_start_time()
    turnos = []
    for turno in resultado:
        turnos.append({"inicio": turno.start, "fin": turno.end, "hablante": turno.speaker})
    return turnos


def asignar_hablantes(frases, turnos, proporcion_minima=0.1):
    # 1) Cada frase de Whisper se queda con el hablante que más se solapa con ella.
    for frase in frases:
        frase["hablante"] = None
        mejor_solape = 0.0
        for turno in turnos:
            solape = min(frase["fin"], turno["fin"]) - max(frase["inicio"], turno["inicio"])
            if solape > mejor_solape:
                mejor_solape = solape
                frase["hablante"] = turno["hablante"]

    # 2) En grabaciones de celular el diarizador crea grupos de una o dos frases
    # (ruido, voces que se pisan). Solo cuentan los hablantes con al menos
    # proporcion_minima de las frases; el resto hereda el hablante anterior.
    conteo = {}
    for frase in frases:
        if frase["hablante"] is not None:
            conteo[frase["hablante"]] = conteo.get(frase["hablante"], 0) + 1
    if not conteo:
        return frases
    principales = []
    for hablante, cantidad in conteo.items():
        if cantidad >= proporcion_minima * len(frases):
            principales.append(hablante)
    if not principales:
        principales = [max(conteo, key=conteo.get)]
    anterior = None
    for frase in frases:
        if frase["hablante"] in principales:
            anterior = frase["hablante"]
        else:
            frase["hablante"] = anterior
    # Si el clip empieza con una frase dudosa, toma el primer hablante principal que aparezca.
    primero = next(frase["hablante"] for frase in frases if frase["hablante"] is not None)
    for frase in frases:
        if frase["hablante"] is None:
            frase["hablante"] = primero

    # 3) Se renombran por orden de aparición: el primero que habla es HABLANTE_1.
    orden = {}
    for frase in frases:
        if frase["hablante"] not in orden:
            orden[frase["hablante"]] = len(orden) + 1
        frase["hablante"] = f"HABLANTE_{orden[frase['hablante']]}"
    return frases


def texto_con_hablantes(frases):
    # Se marca un cambio de hablante solo cuando cambia, no en cada frase.
    partes = []
    hablante_anterior = None
    for frase in frases:
        hablante = frase.get("hablante")
        if hablante and hablante != hablante_anterior:
            partes.append(f"[{hablante}]")
            hablante_anterior = hablante
        partes.append(frase["texto"])
    return " ".join(partes)


def formato_srt(segundos):
    milisegundos = int(round(segundos * 1000))
    horas, milisegundos = divmod(milisegundos, 3_600_000)
    minutos, milisegundos = divmod(milisegundos, 60_000)
    segundos, milisegundos = divmod(milisegundos, 1000)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d},{milisegundos:03d}"


def a_srt(frases, ruta):
    lineas = []
    for numero, frase in enumerate(frases, start=1):
        etiqueta = f"[{frase['hablante']}] " if frase.get("hablante") else ""
        lineas.append(str(numero))
        lineas.append(f"{formato_srt(frase['inicio'])} --> {formato_srt(frase['fin'])}")
        lineas.append(etiqueta + frase["texto"])
        lineas.append("")
    Path(ruta).write_text("\n".join(lineas), encoding="utf-8")


def a_txt(texto, ruta):
    Path(ruta).write_text(texto + "\n", encoding="utf-8")


# --- Seudonimización -------------------------------------------------------

PATRON_DNI = re.compile(r"\b\d{8}\b")
PATRON_TELEFONO = re.compile(r"\b9\d{2}[ -]?\d{3}[ -]?\d{3}\b")
PATRON_CORREO = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
# "me llamo Rosa", "mi nombre es Juan Pérez": la autopresentación es la forma
# más común en que aparece un nombre propio dentro de una entrevista.
PATRON_PRESENTACION = re.compile(
    r"\b((?i:me llamo|mi nombre es))\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,2})"
)


def seudonimizar(texto, nombres_a_reemplazar):
    """Devuelve (texto_seudonimizado, cantidad_de_reemplazos).

    nombres_a_reemplazar es un diccionario {nombre real: seudónimo} que sale de
    la revisión humana; las reglas automáticas cubren DNI, teléfonos, correos y
    autopresentaciones.
    """
    reemplazos = 0
    for nombre, seudonimo in nombres_a_reemplazar.items():
        patron = re.compile(r"\b" + re.escape(nombre) + r"\b", flags=re.IGNORECASE)
        texto, veces = patron.subn(seudonimo, texto)
        reemplazos += veces
    texto, veces = PATRON_PRESENTACION.subn(lambda m: m.group(1) + " [NOMBRE]", texto)
    reemplazos += veces
    texto, veces = PATRON_DNI.subn("[DNI]", texto)
    reemplazos += veces
    texto, veces = PATRON_TELEFONO.subn("[TELEFONO]", texto)
    reemplazos += veces
    texto, veces = PATRON_CORREO.subn("[CORREO]", texto)
    reemplazos += veces
    return texto, reemplazos

