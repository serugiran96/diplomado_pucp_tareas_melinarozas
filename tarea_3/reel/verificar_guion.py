"""Comprueba que las cifras del guion salgan de los datos y que el reel cumpla los requisitos técnicos."""
import json
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
r = json.loads((RAIZ / "datos" / "procesados" / "resultados.json").read_text(encoding="utf-8"))
guion = json.loads((AQUI / "guion.json").read_text(encoding="utf-8"))
texto = " ".join(e["frase"] for e in guion["escenas"])
temp = {f["departamento"]: f for f in r["ranking_temp"]}
ll = {f["departamento"]: f for f in r["ranking_lluvia"]}
e5 = r["era5"]
e5_ll = {f["departamento"]: f for f in e5["lluvia"]}
e5_t = {f["departamento"]: f for f in e5["temp"]}
fallos = []


def afirma(ok, descripcion):
    print(("ok   " if ok else "FALLA"), descripcion)
    if not ok:
        fallos.append(descripcion)


afirma(r["periodos"]["p1"] == [1981, 2000] and r["periodos"]["p2"] == [2006, 2025], "periodos 1981-2000 y 2006-2025")
afirma(round(r["nacional"]["cambio_temp"], 2) == 0.50, f"cambio nacional = {r['nacional']['cambio_temp']:.2f} °C ('medio grado')")
afirma(r["nacional"]["anios_mas_calidos"][0]["anio"] == 2024, "2024 es el año más cálido de la serie")
afirma(round(temp["Ucayali"]["tend_temp"], 2) == 0.47, f"Ucayali {temp['Ucayali']['tend_temp']} °C/década")
afirma(round(temp["Ica"]["tend_temp"], 2) == 0.10, f"Ica {temp['Ica']['tend_temp']} °C/década")
afirma(max(temp.values(), key=lambda f: f["tend_temp"])["departamento"] == "Ucayali", "Ucayali es el mayor en NASA POWER")
afirma(min(temp.values(), key=lambda f: f["tend_temp"])["departamento"] == "Ica", "Ica es el menor en NASA POWER")
afirma(abs(e5["promedio_25_puntos"]["por_decada"] - r["nacional"]["por_decada"]) < 0.03, "ERA5 confirma el promedio nacional")
afirma(e5["spearman_depto"] < 0.6, f"el orden cambia entre fuentes (rho {e5['spearman_depto']:.2f})")
afirma(r["nacional"]["p_lluvia"] > 0.05 and abs(r["nacional"]["cambio_lluvia_pct"]) < 5, "sin tendencia nacional clara de lluvia")
for d in ("Piura", "Tumbes", "Lambayeque"):
    afirma(ll[d]["cambio_lluvia_pct"] < -20 and e5_ll[d]["cambio_era5_pct"] < -20,
           f"{d}: {ll[d]['cambio_lluvia_pct']} % NASA y {e5_ll[d]['cambio_era5_pct']} % ERA5 (más de 20 % menos)")
sens = e5["norte_sin_anios_el_nino"]
afirma(all(sens[d]["era5_pct"] > e5_ll[d]["cambio_era5_pct"] for d in sens), "sin años de El Niño la caída en ERA5 se reduce")
for d in ("Ica", "Ayacucho"):
    afirma(abs(ll[d]["cambio_lluvia_pct"] - e5_ll[d]["cambio_era5_pct"]) > 30, f"{d}: las fuentes difieren ({ll[d]['cambio_lluvia_pct']} % y {e5_ll[d]['cambio_era5_pct']} %)")
afirma(5 <= len(guion["escenas"]) <= 7, f"{len(guion['escenas'])} escenas")
afirma("generada con inteligencia artificial" in texto, "la narración declara la voz con IA")

for nombre, carpeta in (("reel.mp4", AQUI), ("reel_borrador.mp4", AQUI)):
    mp4 = carpeta / nombre
    if not mp4.exists():
        continue
    info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-i", str(mp4)], capture_output=True, text=True).stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
    seg = int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3])
    afirma(45 <= seg <= 75, f"{nombre}: {seg:.1f} s")
    afirma("1080x1920" in info, f"{nombre}: 1080x1920")
    afirma("Audio:" in info, f"{nombre}: con audio")

if fallos:
    sys.exit(f"{len(fallos)} comprobaciones fallaron")
print("Todo coincide con los datos.")
