# Modelos usados

Los pesos **no se versionan** (pesan de 26 MB a 1,6 GB): se descargan solos la primera vez o con los comandos indicados. Aquí queda la configuración exacta de cada uno.

| Uso | Modelo | Versión / configuración | Descarga | Licencia |
|---|---|---|---|---|
| OCR (elegido) | PaddleOCR PP-OCRv6_medium (detección y reconocimiento) | PaddleOCR 3.7.0, `lang="es"`, sin clasificador de orientación ni desdoblado (UVDoc), imagen ≤2500 px | automática (Hugging Face, `PaddlePaddle/`) | Apache 2.0 |
| OCR (línea base) | PaddleOCR por defecto | igual, con orientación de página, desdoblado y orientación de línea activados | automática | Apache 2.0 |
| OCR (alternativo) | EasyOCR (CRAFT + reconocedor latino `latin_g2`) | EasyOCR 1.7.2, `["es"]`, CPU | automática (GitHub de EasyOCR) | Apache 2.0 |
| ASR (elegido) | faster-whisper `large-v3-turbo` | int8, CPU, `beam_size=5`, VAD Silero (`min_silence_duration_ms=500`), `language="es"`, sin condicionar en el texto previo | automática (`mobiuslabsgmbh/faster-whisper-large-v3-turbo`) | MIT |
| ASR (línea base) | faster-whisper `small` | mismas opciones | automática (`Systran/faster-whisper-small`) | MIT |
| ASR (alternativo) | NVIDIA Parakeet TDT 0.6B v3, int8 ONNX | sherpa-onnx 2.0.0, tramos de voz ≤20 s cortados con el mismo VAD | [sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2) → `modelos/` | CC BY 4.0 |
| Diarización: segmentación | pyannote-segmentation-3.0 (ONNX) | sherpa-onnx 2.0.0 | [sherpa-onnx-pyannote-segmentation-3-0.tar.bz2](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2) → `modelos/diarizacion/` | MIT |
| Diarización: huella de voz | 3D-Speaker ERes2Net base | umbral 0,7; `n_hablantes=3` fijado en `clip_011` | [3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx](https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx) → `modelos/diarizacion/` | Apache 2.0 |
| Extracción estructurada | Qwen2.5-0.5B-Instruct | transformers, CPU, `float32`, decodificación determinista, `max_new_tokens=220` | automática (`Qwen/Qwen2.5-0.5B-Instruct`) | Apache 2.0 |
