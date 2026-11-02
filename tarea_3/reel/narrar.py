"""Guion -> narración -> subtítulos. Sigue el flujo de la Sesión 15 (Qwen3-TTS + Whisper).

    python reel/narrar.py --voz reel/mi_voz.m4a       # voz clonada de la autora (reel final)
    python reel/narrar.py --provisional               # voz del sistema, solo para el borrador

En guion.json las cifras se escriben {0.47|cero coma cuarenta y siete}: lo de la izquierda va a los
subtítulos y lo de la derecha a la voz, para que la pantalla muestre dígitos y las cifras se pronuncien bien.

Salidas en reel/ (o reel/.borrador/ con --provisional): narracion.wav, tiempos.json y subtitulos.srt
"""
import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf

AQUI = Path(__file__).resolve().parent
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
TTS = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
ASR = "large-v3-turbo"
PAUSA, INICIO, FINAL = 0.35, 0.3, 0.9   # silencios en segundos
DUR_MIN, DUR_MAX = 45, 75
MAX_WER = 0.25


def partes(marcada):
    """Devuelve la frase para la voz y la lista de (texto_pantalla, palabras_voz)."""
    voz, fichas = [], []
    for trozo in re.split(r"(\{[^}]+\})", marcada):
        if trozo.startswith("{"):
            pantalla, dicho = trozo[1:-1].split("|")
            voz.append(dicho)
            fichas.append((pantalla, dicho.split()))
        else:
            voz.append(trozo)
            fichas.extend((p, [p]) for p in trozo.split())
    return "".join(voz), fichas


def normalizar(s):
    s = unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^\w\s]", " ", s).strip()


def a_mono(ruta, sr=16000):
    crudo = subprocess.run([FFMPEG, "-v", "error", "-i", str(ruta), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.float32)


def remuestrear(w, sr, sr_nuevo=16000):
    return np.interp(np.arange(0, len(w), sr / sr_nuevo), np.arange(len(w)), w).astype(np.float32)


def quitar_arranque(w, sr):
    """Qwen3 abre cada toma con un soplido de unos 0.2 s antes del habla: se silencia sin mover los tiempos."""
    marco = int(.02 * sr)
    pico = float(np.abs(w).max()) or 1
    niveles = [20 * np.log10(np.sqrt((w[k:k + marco] ** 2).mean()) / pico + 1e-9) for k in range(0, min(len(w), int(1.5 * sr)) - marco, marco)]
    silencio = next((k for k in range(min(50, len(niveles) - 2)) if max(niveles[k:k + 3]) < -43), None)
    if silencio is None:
        return w
    habla = next((k for k in range(silencio, len(niveles)) if niveles[k] > -38), None)
    if habla is None:
        return w
    corte = max(0, habla - 2) * marco
    limpio = np.array(w, np.float32)
    limpio[:corte] = 0
    rampa = min(int(.01 * sr), len(limpio) - corte)
    limpio[corte:corte + rampa] *= np.linspace(0, 1, rampa, dtype=np.float32)
    return limpio


class Whisper:
    def __init__(self):
        from faster_whisper import WhisperModel
        self.m = WhisperModel(ASR, device="cpu", compute_type="int8")

    def texto(self, audio16k, contexto=None):
        return " ".join(s.text.strip() for s in self.m.transcribe(audio16k, language="es", initial_prompt=contexto)[0])

    def palabras(self, audio16k, contexto):
        segs, _ = self.m.transcribe(audio16k, language="es", word_timestamps=True, initial_prompt=contexto)
        return [(w.start, w.end, w.word.strip()) for s in segs for w in s.words if w.word.strip()]


def wer(ref, oido):
    a, b = normalizar(ref).split(), normalizar(oido).split()
    return 1 - difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


class VozClonada:
    def __init__(self, referencia, asr, device):
        import torch
        from qwen_tts import Qwen3TTSModel
        audio = a_mono(referencia)
        seg = len(audio) / 16000
        print(f"Referencia: {seg:.1f} s", flush=True)
        if not 8 <= seg <= 40:
            sys.exit(f"La grabación dura {seg:.1f} s; el enunciado pide entre 15 y 25 s.")
        self.tts = Qwen3TTSModel.from_pretrained(TTS, device_map=device, dtype=torch.float32)
        texto = asr.texto(audio)
        print(f"Transcripción de la referencia: {texto}", flush=True)
        self.prompt = self.tts.create_voice_clone_prompt(ref_audio=(audio, 16000), ref_text=texto)

    def decir(self, frase):
        wavs, sr = self.tts.generate_voice_clone(text=[frase], language=["Spanish"], voice_clone_prompt=self.prompt)
        return quitar_arranque(np.asarray(wavs[0], np.float32), sr), sr


class VozSistema:
    """Solo para probar el montaje; el reel final no usa esta voz."""

    def decir(self, frase):
        with tempfile.TemporaryDirectory() as t:
            ruta = Path(t) / "x.aiff"
            subprocess.run(["say", "-v", "Paulina", "-r", "178", "-o", str(ruta), frase], check=True)
            return a_mono(ruta, 24000), 24000


def alinear(fichas, palabras, ini, fin):
    """Tiempos por palabra de Whisper sobre el texto del guion; lo no reconocido se interpola."""
    plano, dueno = [], []
    for i, (_, dichas) in enumerate(fichas):
        for d in dichas:
            for n in normalizar(d).split():
                plano.append(n)
                dueno.append(i)
    oidas = [normalizar(w[2]) for w in palabras]
    t = [None] * len(plano), [None] * len(plano)
    for a in difflib.SequenceMatcher(None, plano, oidas, autojunk=False).get_matching_blocks():
        for k in range(a.size):
            t[0][a.a + k], t[1][a.a + k] = palabras[a.b + k][0], palabras[a.b + k][1]
    x = np.arange(len(plano))
    conocidos = [i for i in x if t[0][i] is not None]
    if conocidos:
        ini_i = np.interp(x, conocidos, [t[0][i] for i in conocidos])
        fin_i = np.interp(x, conocidos, [t[1][i] for i in conocidos])
        if conocidos[0] > 0:           # extremos sin reconocer: se reparten hasta el borde de la escena
            ini_i[:conocidos[0]] = np.linspace(ini, ini_i[conocidos[0]], conocidos[0], endpoint=False)
        if conocidos[-1] < len(plano) - 1:
            fin_i[conocidos[-1] + 1:] = np.linspace(fin_i[conocidos[-1]], fin, len(plano) - conocidos[-1])[1:]
    else:
        ini_i = np.linspace(ini, fin, len(plano), endpoint=False)
        fin_i = ini_i + (fin - ini) / max(1, len(plano))
    salida = []
    for i, (texto, _) in enumerate(fichas):
        idx = [k for k, d in enumerate(dueno) if d == i]
        if idx:
            salida.append({"t": texto, "ini": round(float(ini_i[idx[0]]), 3), "fin": round(float(fin_i[idx[-1]]), 3)})
        elif salida:                    # signo suelto: se pega a la palabra anterior
            salida[-1]["t"] += texto
    # Mantiene el orden aunque Whisper devuelva tiempos que se traslapen
    for a, b in zip(salida, salida[1:]):
        b["ini"] = max(b["ini"], a["ini"] + 0.02)
        a["fin"] = min(max(a["fin"], a["ini"] + 0.05), b["ini"])
    return salida


def bloques(palabras, max_palabras=4, max_letras=26):
    res, actual = [], []
    for p in palabras:
        if actual and (len(actual) >= max_palabras or sum(len(a["t"]) + 1 for a in actual) + len(p["t"]) > max_letras):
            res.append(actual)
            actual = []
        actual.append(p)
        if re.search(r"[.,:;?!]$", p["t"]):
            res.append(actual)
            actual = []
    if actual:
        res.append(actual)
    return [{"t": " ".join(a["t"] for a in b), "ini": b[0]["ini"], "fin": b[-1]["fin"]} for b in res]


def srt(bs):
    def h(s):
        ms = int(round(s * 1000))
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    return "\n".join(f"{i}\n{h(b['ini'])} --> {h(b['fin'])}\n{b['t']}\n" for i, b in enumerate(bs, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz")
    ap.add_argument("--provisional", action="store_true")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--guion", default=str(AQUI / "guion.json"))
    ap.add_argument("--salidas")
    a = ap.parse_args()
    if not a.voz and not a.provisional:
        ap.error("Indica --voz RUTA o --provisional")
    salidas = Path(a.salidas) if a.salidas else (AQUI / ".borrador" if a.provisional else AQUI)
    salidas.mkdir(exist_ok=True)

    t0 = time.time()
    guion = json.loads(Path(a.guion).read_text(encoding="utf-8"))
    asr = Whisper()
    voz = VozSistema() if a.provisional else VozClonada(a.voz, asr, a.device)

    sr, wavs, datos = None, [], []
    for i, e in enumerate(guion["escenas"], 1):
        frase, fichas = partes(e["frase"])
        for intento in range(3):
            w, sr = voz.decir(frase)
            oido = asr.texto(remuestrear(w, sr), frase)
            error = wer(frase, oido)
            print(f"[{time.time() - t0:5.0f}s] escena {i}: {len(w) / sr:.1f} s, error de lectura {error:.0%}", flush=True)
            if error <= MAX_WER or a.provisional:
                break
        wavs.append(w)
        datos.append({"id": e["id"], "frase": frase, "fichas": fichas, "error": round(error, 3), "oido": oido})

    total = INICIO + sum(len(w) / sr for w in wavs) + PAUSA * len(wavs) + FINAL
    factor = 1.0
    if total > DUR_MAX - 1:             # acelera sin cambiar el tono para no pasar del máximo
        factor = (total - INICIO - FINAL - PAUSA * len(wavs)) / (DUR_MAX - 1 - INICIO - FINAL - PAUSA * len(wavs))
        print(f"Duración {total:.1f} s > {DUR_MAX}: se acelera x{factor:.3f}", flush=True)
        wavs = [np.frombuffer(subprocess.run(
            [FFMPEG, "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", f"atempo={factor}", "-f", "f32le", "-"],
            input=w.tobytes(), capture_output=True, check=True).stdout, np.float32) for w in wavs]

    trozos, t = [np.zeros(int(INICIO * sr), np.float32)], INICIO
    escenas, todos = [], []
    for w, d in zip(wavs, datos):
        dur = len(w) / sr
        pal = asr.palabras(remuestrear(w, sr), d["frase"])
        pal = [(p[0] + t, p[1] + t, p[2]) for p in pal]
        al = alinear(d["fichas"], pal, t, t + dur)
        al[0]["ini"] = max(al[0]["ini"], t + int(np.argmax(np.abs(w) > 1e-6)) / sr)   # el subtítulo espera a la primera palabra
        al[0]["fin"] = max(al[0]["fin"], al[0]["ini"] + 0.05)
        todos.extend(al)
        escenas.append({"id": d["id"], "ini": round(t, 3), "fin": round(t + dur, 3), "error": d["error"], "oido": d["oido"]})
        trozos += [w, np.zeros(int(PAUSA * sr), np.float32)]
        t += dur + PAUSA
    trozos.append(np.zeros(int(FINAL * sr), np.float32))
    audio = np.concatenate(trozos)
    pico = float(np.abs(audio).max()) or 1
    audio = audio * min(0.95 / pico, 4.0)

    sf.write(salidas / "narracion.wav", audio, sr)
    bs = bloques(todos)
    (salidas / "subtitulos.srt").write_text(srt(bs), encoding="utf-8")
    dur = len(audio) / sr
    (salidas / "tiempos.json").write_text(json.dumps(
        {"duracion": round(dur, 3), "provisional": a.provisional, "aceleracion": round(factor, 3),
         "escenas": escenas, "subtitulos": bs}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Listo en {time.time() - t0:.0f} s. Duración {dur:.1f} s ({'dentro' if DUR_MIN <= dur <= DUR_MAX else 'FUERA'} de {DUR_MIN}-{DUR_MAX} s)", flush=True)
    malas = [e["id"] for e in escenas if e["error"] > MAX_WER]
    if malas and not a.provisional:
        print(f"REVISAR: Whisper entendió mal las escenas {malas}", flush=True)


if __name__ == "__main__":
    main()
