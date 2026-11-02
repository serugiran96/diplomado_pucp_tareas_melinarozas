"""Música de fondo original, sintetizada aquí: no depende de ninguna licencia de terceros (se libera como CC0).

Base lenta de acordes (la menor, fa, do, sol) con un pulso suave. Salida: reel/recursos/musica.flac
"""
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
DUR = 80.0
TEMPO = 72
SALIDA = Path(__file__).resolve().parent / "recursos" / "musica.flac"
ACORDES = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]   # MIDI


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def nota(f, dur, ataque, caida, armonicos):
    t = np.arange(int(dur * SR)) / SR
    onda = sum(a * np.sin(2 * np.pi * f * k * t + k) for k, a in armonicos)
    env = np.minimum(1, t / ataque) * np.minimum(1, (dur - t) / caida)
    return onda * env


def poner(pista, s, t0):
    i = int(t0 * SR)
    fin = min(len(pista), i + len(s))
    pista[i:fin] += s[:fin - i]


def main():
    izq, der = np.zeros(int(DUR * SR)), np.zeros(int(DUR * SR))
    pulso = 60 / TEMPO
    compas = pulso * 4 * 2                        # cada acorde dura dos compases
    rng = np.random.default_rng(7)
    t, i = 0.0, 0
    while t < DUR:
        acorde = ACORDES[i % 4]
        for j, m in enumerate(acorde):            # colchón armónico
            s = nota(hz(m), compas + 1.5, 1.6, 1.8, [(1, 1), (2, .28), (3, .08)]) * .10
            pan = .35 + .1 * j
            poner(izq, s * (1 - pan), t)
            poner(der, s * pan, t)
        poner(izq, nota(hz(acorde[0] - 12), compas, .4, 1.0, [(1, 1), (2, .2)]) * .16, t)   # bajo
        poner(der, nota(hz(acorde[0] - 12), compas, .4, 1.0, [(1, 1), (2, .2)]) * .16, t)
        for b in range(8):                        # arpegio discreto
            m = acorde[rng.integers(0, 4)] + 12
            s = nota(hz(m), pulso * 1.7, .01, pulso * 1.5, [(1, 1), (2, .15)]) * .055
            pan = rng.uniform(.25, .75)
            poner(izq, s * (1 - pan), t + b * pulso)
            poner(der, s * pan, t + b * pulso)
        t += compas
        i += 1
    audio = np.stack([izq, der], axis=1)
    audio *= np.minimum(1, np.arange(len(audio)) / (2.0 * SR))[:, None]
    audio = np.tanh(audio * 1.2)
    audio *= 0.8 / np.abs(audio).max()
    SALIDA.parent.mkdir(exist_ok=True)
    sf.write(SALIDA, audio.astype(np.float32), SR, subtype="PCM_16", format="FLAC")
    print(SALIDA, f"{len(audio) / SR:.0f} s")


if __name__ == "__main__":
    main()
