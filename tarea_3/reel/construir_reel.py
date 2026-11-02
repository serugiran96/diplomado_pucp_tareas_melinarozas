"""Monta el reel 1080x1920 con Pillow y ffmpeg a partir de narracion.wav y tiempos.json.

    python reel/construir_reel.py               # reel final: reel/reel.mp4
    python reel/construir_reel.py --provisional # borrador con voz del sistema y marca visible

Las cifras de los gráficos se leen de web/data/clima.json, no se escriben a mano.
"""
import argparse
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
REC = AQUI / "recursos"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ANCHO, ALTO, FPS = 1080, 1920, 30
MARGEN = 72
FONDO, TEXTO, SUAVE = (18, 17, 15), (246, 243, 236), (190, 184, 172)
AZUL, ROJO, CAFE = (85, 152, 231), (236, 96, 84), (224, 150, 72)
FUNDIDO = 0.35
CIERRE_DESDE = 1500   # píxeles desde el inicio de la captura de celular: empieza en los indicadores
URL = "serugiran96.github.io/diplomado_pucp_tareas_melinarozas"
MUSICA_GANANCIA = 0.11   # unos 19 dB por debajo de la voz


def fuente(nombre, tam, peso):
    f = ImageFont.truetype(str(REC / f"{nombre}.ttf"), tam)
    f.set_variation_by_axes([peso])
    return f


F = {}
def letra(nombre, tam, peso=700):
    k = (nombre, tam, peso)
    if k not in F:
        F[k] = fuente(nombre, tam, peso)
    return F[k]


def suave(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mezcla(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rampa(v, vmax, neg, pos, medio=(58, 56, 53)):
    t = min(1, abs(v) / vmax) ** 0.8
    return mezcla(medio, pos if v > 0 else neg, t)


def centrado(d, y, texto, f, color=TEXTO, x=ANCHO / 2):
    caja = d.textbbox((0, 0), texto, font=f)
    d.text((x - (caja[2] - caja[0]) / 2 - caja[0], y - caja[1]), texto, font=f, fill=color)
    return y + (caja[3] - caja[1])


def envolver(d, texto, f, ancho):
    lineas, actual = [], ""
    for p in texto.split():
        prueba = f"{actual} {p}".strip()
        if d.textlength(prueba, font=f) > ancho and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = prueba
    return lineas + [actual]


def parrafo(d, y, texto, f, color=TEXTO, ancho=ANCHO - 2 * MARGEN, salto=1.22, centrar=True):
    for l in envolver(d, texto, f, ancho):
        if centrar:
            centrado(d, y, l, f, color)
        else:
            d.text((MARGEN, y), l, font=f, fill=color)
        y += int(f.size * salto)
    return y


class Datos:
    def __init__(self):
        c = json.loads((RAIZ / "web" / "data" / "clima.json").read_text(encoding="utf-8"))
        self.c, self.r = c, c["resultados"]
        self.anios = c["anios"]
        m = np.array(c["nacional"]["temp_media"]).reshape(-1, 12).mean(axis=1)
        base = m[(np.array(self.anios) >= 1991) & (np.array(self.anios) <= 2020)].mean()
        self.nac, self.anom = m, m - base
        self.temp = {f["departamento"]: f for f in self.r["ranking_temp"]}
        self.lluvia = {f["departamento"]: f for f in self.r["ranking_lluvia"]}
        self.geo = json.loads((RAIZ / "web" / "data" / "peru.geojson").read_text(encoding="utf-8"))["features"]


def anillos(g):
    return g["coordinates"] if g["type"] == "Polygon" else [p for pol in g["coordinates"] for p in pol]


def pintar_mapa(datos, color, ancho, alto, resalta=()):
    esc = 2
    todos = [c for f in datos.geo for a in anillos(f["geometry"]) for c in a]
    xs, ys = [c[0] for c in todos], [c[1] for c in todos]
    k = min((ancho - 20) * esc / (max(xs) - min(xs)), (alto - 20) * esc / (max(ys) - min(ys)))
    ox = (ancho * esc - k * (max(xs) - min(xs))) / 2
    oy = (alto * esc - k * (max(ys) - min(ys))) / 2
    im = Image.new("RGBA", (ancho * esc, alto * esc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pos = {}
    pares = lambda a: [(ox + (x - min(xs)) * k, oy + (max(ys) - y) * k) for x, y in a]
    for f in datos.geo:
        nombre = f["properties"]["nombre"]
        for i, a in enumerate(anillos(f["geometry"])):
            d.polygon(pares(a), fill=color(nombre) + (255,), outline=FONDO + (255,), width=3)
    for f in datos.geo:
        nombre = f["properties"]["nombre"]
        puntos = [c for a in anillos(f["geometry"]) for c in a]
        px = pares(puntos)
        pos[nombre] = (sum(p[0] for p in px) / len(px) / esc, sum(p[1] for p in px) / len(px) / esc)
        if nombre in resalta:
            for a in anillos(f["geometry"]):
                d.line(pares(a) + [pares(a)[0]], fill=TEXTO + (255,), width=7)
    return im.resize((ancho, alto), Image.LANCZOS), pos


def foto(nombre, t, oscuro=0.45, zoom=(1.0, 1.12), desplaza=(0.5, 0.5)):
    """Efecto Ken Burns sobre una foto recortada a 9:16."""
    im = _FOTOS.setdefault(nombre, Image.open(REC / "fotos" / f"{nombre}.jpg").convert("RGB"))
    z = zoom[0] + (zoom[1] - zoom[0]) * t
    alto = im.height / z
    ancho = alto * ANCHO / ALTO
    x = (im.width - ancho) * desplaza[0]
    y = (im.height - alto) * desplaza[1]
    r = im.resize((ANCHO, ALTO), Image.BILINEAR, box=(x, y, x + ancho, y + alto))
    return Image.blend(r, Image.new("RGB", (ANCHO, ALTO), FONDO), oscuro)


_FOTOS = {}


def ficha(d, texto, y, f=None, x=MARGEN):
    f = f or letra("PublicSans", 34, 600)
    a = d.textlength(texto, font=f)
    d.rounded_rectangle((x, y, x + a + 36, y + 58), radius=12, fill=(0, 0, 0))
    d.text((x + 18, y + 10), texto, font=f, fill=TEXTO)


class Reel:
    def __init__(self, tiempos, provisional):
        self.t = tiempos
        self.d = Datos()
        self.prov = provisional
        self.esc = {e["id"]: e for e in tiempos["escenas"]}
        self.creditos = json.loads((REC / "fotos" / "creditos.json").read_text(encoding="utf-8"))
        d = self.d
        vmax = max(abs(f["tend_temp"]) for f in d.temp.values())
        mapa_a, mapa_h = 880, 1010
        self.map_t, self.pos = pintar_mapa(d, lambda n: rampa(d.temp[n]["tend_temp"], vmax, AZUL, ROJO), mapa_a, mapa_h)
        self.map_t2, _ = pintar_mapa(d, lambda n: rampa(d.temp[n]["tend_temp"], vmax, AZUL, ROJO), mapa_a, mapa_h, ("Ucayali", "Ica"))
        norte = d.r["era5"]["caida_ambas_10"]
        self.map_l2, _ = pintar_mapa(d, lambda n: CAFE if n in norte else (58, 56, 53), mapa_a, mapa_h, tuple(norte))
        self.map_xy = ((ANCHO - mapa_a) // 2, 400)
        cap = sorted((REC).glob("dashboard_*.png"))
        self.capturas = [Image.open(c).convert("RGB") for c in cap]
        self.franjas_im = self._franjas()

    def _franjas(self):
        d = self.d
        n = len(d.anios)
        im = Image.new("RGB", (ANCHO, ALTO), FONDO)
        dib = ImageDraw.Draw(im)
        for i, a in enumerate(d.anom):
            c = rampa(a, 1.2, (28, 88, 170), (190, 34, 34), (232, 228, 220))
            dib.rectangle((i * ANCHO / n, 0, (i + 1) * ANCHO / n, ALTO), fill=c)
        return im

    # --- Escenas: cada una recibe t en 0..1 y el tiempo en segundos desde su inicio ---
    def gancho(self, t, s):
        d = self.d
        n = len(d.anios)
        visibles = suave(s / 2.8) * n
        im = Image.new("RGB", (ANCHO, ALTO), FONDO)
        ancho = int(ANCHO * visibles / n)
        if ancho > 0:
            im.paste(self.franjas_im.crop((0, 0, ancho, ALTO)), (0, 0))
        dib = ImageDraw.Draw(im, "RGBA")
        dib.rectangle((0, 470, ANCHO, 1030), fill=(0, 0, 0, 165))
        anio = d.anios[min(n - 1, int(visibles))]
        centrado(dib, 515, str(anio), letra("Oswald", 190, 700))
        y = parrafo(dib, 765, "45 años de temperatura", letra("PublicSans", 58, 700))
        parrafo(dib, y + 4, "en los 25 departamentos", letra("PublicSans", 58, 700))
        centrado(dib, 955, "Cada franja es un año", letra("PublicSans", 36, 500), SUAVE)
        return im

    def nacional(self, t, s):
        d = self.d
        im = Image.new("RGB", (ANCHO, ALTO), FONDO)
        dib = ImageDraw.Draw(im, "RGBA")
        y = centrado(dib, 240, f"+{d.r['nacional']['cambio_temp']:.2f} °C", letra("Oswald", 190, 700))
        parrafo(dib, y + 34, "2006-2025 frente a 1981-2000", letra("PublicSans", 42, 500), SUAVE)
        x0, x1, y0, y1 = MARGEN + 60, ANCHO - MARGEN - 10, 620, 1240
        vmin, vmax = 18.4, 21.3
        X = lambda a: x0 + (a - 1981) / 44 * (x1 - x0)
        Y = lambda v: y1 - (v - vmin) / (vmax - vmin) * (y1 - y0)
        fg = letra("PublicSans", 30, 500)
        for v in (19, 20, 21):
            dib.line((x0, Y(v), x1, Y(v)), fill=(70, 68, 64, 255), width=2)
            dib.text((MARGEN - 12, Y(v) - 18), f"{v} °C", font=fg, fill=SUAVE)
        for a in (1981, 2000, 2025):
            centrado(dib, y1 + 16, str(a), fg, SUAVE, x=min(X(a), x1 - 30))
        visibles = max(2, int(suave(s / 4.5) * 45))
        pts = [(X(a), Y(v)) for a, v in zip(d.anios[:visibles], d.nac[:visibles])]
        dib.line(pts, fill=ROJO + (255,), width=7, joint="curve")
        px, py = pts[-1]
        dib.ellipse((px - 11, py - 11, px + 11, py + 11), fill=TEXTO)
        if visibles >= 44:
            i = d.anios.index(2024)
            dib.ellipse((X(2024) - 13, Y(d.nac[i]) - 13, X(2024) + 13, Y(d.nac[i]) + 13), fill=TEXTO)
            f = letra("PublicSans", 40, 700)
            texto = f"2024: {d.nac[i]:.1f} °C"
            dib.text((X(2024) - dib.textlength(texto, font=f) - 26, Y(d.nac[i]) - 28), texto, font=f, fill=TEXTO)
        return im

    def desigual(self, t, s):
        d = self.d
        if s < 2.0:                       # el río Ucayali visto desde el espacio
            im = foto("ucayali", s / 2.0, oscuro=0.2, zoom=(1.0, 1.1), desplaza=(0.45, 0.45))
            dib = ImageDraw.Draw(im, "RGBA")
            ficha(dib, "Río Ucayali desde la Estación Espacial. NASA", 1300, letra("PublicSans", 30, 500))
        else:
            im = Image.new("RGB", (ANCHO, ALTO), FONDO)
            dib = ImageDraw.Draw(im, "RGBA")
        mezcla_m = suave((s - 2.0) / 0.5)
        if s >= 2.0:
            im.paste(self.map_t2, self.map_xy, self.map_t2.split()[3].point(lambda v: int(v * mezcla_m)))
            dib = ImageDraw.Draw(im, "RGBA")
            centrado(dib, 175, "Tendencia por década", letra("PublicSans", 46, 600), SUAVE)
            self._dato(dib, "Ucayali", f"+{d.temp['Ucayali']['tend_temp']:.2f} °C", (ANCHO - 400, 520), s - 2.3)
            self._dato(dib, "Ica", f"+{d.temp['Ica']['tend_temp']:.2f} °C", (MARGEN, 1120), s - 3.3)
            self._guia(dib, "Ucayali", (ANCHO - 240, 680), s - 2.3)
            self._guia(dib, "Ica", (MARGEN + 170, 1120), s - 3.3)
            e5 = {f["departamento"]: f["tend_era5"] for f in d.r["era5"]["temp"]}
            if s > 5.5:
                texto = f"En ERA5: Ucayali {e5['Ucayali']:+.2f} °C · Ica {e5['Ica']:+.2f} °C".replace("-", "−")
                ficha(dib, texto, 1310, letra("PublicSans", 32, 600), (ANCHO - dib.textlength(texto, font=letra("PublicSans", 32, 600)) - 36) / 2)
        return im

    def _dato(self, dib, nombre, valor, xy, s):
        if s < 0:
            return
        a = int(255 * suave(s / 0.4))
        x, y = xy
        dib.rounded_rectangle((x, y, x + 330, y + 160), radius=18, fill=(0, 0, 0, int(a * .82)))
        dib.text((x + 22, y + 12), nombre, font=letra("PublicSans", 40, 600), fill=TEXTO + (a,))
        dib.text((x + 22, y + 60), valor, font=letra("Oswald", 72, 700), fill=TEXTO + (a,))

    def _guia(self, dib, nombre, xy, s):
        if s < 0:
            return
        a = int(255 * suave(s / 0.4))
        cx, cy = self.pos[nombre]
        dib.line((xy[0], xy[1], self.map_xy[0] + cx, self.map_xy[1] + cy), fill=TEXTO + (a,), width=3)

    def lluvia(self, t, s):
        d = self.d
        im = Image.new("RGB", (ANCHO, ALTO), FONDO)
        base = Image.blend(self.map_t, self.map_l2, suave(s / 1.0))
        im.paste(base, self.map_xy, base.split()[3])
        dib = ImageDraw.Draw(im, "RGBA")
        centrado(dib, 175, "Menos lluvia en ambas fuentes", letra("PublicSans", 50, 700))
        centrado(dib, 245, "2006-2025 frente a 1981-2000", letra("PublicSans", 36, 500), SUAVE)
        e5 = {f["departamento"]: f["cambio_era5_pct"] for f in d.r["era5"]["lluvia"]}
        x, y = 420, 450
        a = int(255 * suave((s - 1.0) / 0.5))
        if a > 0:
            dib.rounded_rectangle((x, y, ANCHO - 40, y + 330), radius=20, fill=(0, 0, 0, int(a * .85)))
            fc = letra("PublicSans", 32, 600)
            dib.text((x + 280, y + 20), "NASA", font=fc, fill=SUAVE + (a,))
            dib.text((x + 450, y + 20), "ERA5", font=fc, fill=SUAVE + (a,))
            for k, n in enumerate(("Piura", "Tumbes", "Lambayeque")):
                yy = y + 80 + k * 80
                dib.text((x + 22, yy + 12), n, font=letra("PublicSans", 34, 600), fill=TEXTO + (a,))
                for xx, v in ((x + 280, d.lluvia[n]["cambio_lluvia_pct"]), (x + 450, e5[n])):
                    dib.text((xx, yy), f"{v:+.0f} %".replace("-", "−"), font=letra("Oswald", 52, 600), fill=TEXTO + (a,))
        return im

    def cautela(self, t, s):
        d = self.d
        im = foto("ica", min(1, s / 7), oscuro=0.35, zoom=(1.0, 1.08), desplaza=(0.5, 0.55))
        cambio = suave((t - 0.45) / 0.12)      # Ica es desierto costero; Ayacucho, sierra
        if cambio > 0:
            im = Image.blend(im, foto("andes", min(1, s / 7), oscuro=0.35, zoom=(1.0, 1.08), desplaza=(0.55, 0.5)), cambio)
        dib = ImageDraw.Draw(im, "RGBA")
        dib.rounded_rectangle((MARGEN - 12, 360, ANCHO - MARGEN + 12, 1010), radius=24, fill=(0, 0, 0, 185))
        centrado(dib, 400, "Las fuentes no coinciden", letra("PublicSans", 50, 700))
        centrado(dib, 470, "Cambio de la lluvia, 2006-2025 frente a 1981-2000", letra("PublicSans", 30, 500), SUAVE)
        e5 = {f["departamento"]: f["cambio_era5_pct"] for f in d.r["era5"]["lluvia"]}
        for k, n in enumerate(("Ica", "Ayacucho")):
            y = 550 + k * 225
            centrado(dib, y, n, letra("PublicSans", 44, 600))
            for x, rot, v in ((ANCHO * .32, "NASA", d.lluvia[n]["cambio_lluvia_pct"]), (ANCHO * .68, "ERA5", e5[n])):
                centrado(dib, y + 62, f"{v:+.0f} %".replace("-", "−"), letra("Oswald", 92, 700), TEXTO, x=x)
                centrado(dib, y + 170, rot, letra("PublicSans", 28, 500), SUAVE, x=x)
        pie = "Foto: desierto de Ica, P. Špindler (CC BY 3.0)" if cambio < 0.5 else "Foto: Andes del Perú desde el espacio, NASA"
        ficha(dib, pie, 1040, letra("PublicSans", 28, 500), MARGEN - 12)
        return im

    def cierre(self, t, s):
        im = Image.new("RGB", (ANCHO, ALTO), FONDO)
        if self.capturas:
            mitad = (self.t["duracion"] - self.esc["cierre"]["ini"]) / 2
            cap = self.capturas[0 if s < mitad or len(self.capturas) == 1 else 1]
            fx, fy, fa, fh = 150, 175, 780, 985
            esc = fa / cap.width
            alto_v = int(fh / esc)
            inicio = CIERRE_DESDE
            pan = suave((s % mitad) / mitad)
            y = int(min(cap.height - alto_v, inicio + pan * 1500))
            r = cap.resize((fa, fh), Image.BILINEAR, box=(0, y, cap.width, y + alto_v))
            mascara = Image.new("L", (fa, fh), 0)
            ImageDraw.Draw(mascara).rounded_rectangle((0, 0, fa, fh), radius=36, fill=255)
            im.paste(r, (fx, fy), mascara)
            ImageDraw.Draw(im).rounded_rectangle((fx - 4, fy - 4, fx + fa + 4, fy + fh + 4), radius=40, outline=(90, 88, 84), width=4)
        dib = ImageDraw.Draw(im, "RGBA")
        centrado(dib, 102, "Explora tu departamento", letra("PublicSans", 50, 700))
        f = letra("PublicSans", 32, 600)
        y = 1195
        y = parrafo(dib, y, "Dashboard interactivo:", letra("PublicSans", 30, 500), SUAVE)
        for l in ("serugiran96.github.io/", "diplomado_pucp_tareas_melinarozas"):
            centrado(dib, y, l, f)
            y += 42
        return im

    # --- Capas comunes ---
    def capas(self, im, seg):
        dib = ImageDraw.Draw(im, "RGBA")
        aviso = "Borrador: voz provisional del sistema" if self.prov else "Voz generada con IA a partir de la voz de la autora"
        f = letra("PublicSans", 28, 600)
        a = dib.textlength(aviso, font=f)
        dib.rounded_rectangle(((ANCHO - a) / 2 - 18, 34, (ANCHO + a) / 2 + 18, 84), radius=12, fill=(0, 0, 0, 200))
        dib.text(((ANCHO - a) / 2, 42), aviso, font=f, fill=(255, 214, 102) if self.prov else TEXTO)
        for b in self.t["subtitulos"]:
            if b["ini"] - 0.03 <= seg <= b["fin"] + 0.12:
                fs = letra("PublicSans", 54, 700)
                lineas = envolver(dib, b["t"], fs, ANCHO - 2 * MARGEN - 40)
                alto = len(lineas) * 68 + 28
                y = 1400
                ancho_max = max(dib.textlength(l, font=fs) for l in lineas)
                dib.rounded_rectangle(((ANCHO - ancho_max) / 2 - 26, y, (ANCHO + ancho_max) / 2 + 26, y + alto), radius=16, fill=(0, 0, 0, 215))
                for i, l in enumerate(lineas):
                    centrado(dib, y + 16 + i * 68, l, fs)
                break
        fuente_t = "Datos: NASA POWER 1981-2025, contraste con ERA5"
        ff = letra("PublicSans", 27, 500)
        centrado(dib, 1610, fuente_t, ff, SUAVE)
        return im

    def creditos_finales(self, dib):
        f = letra("PublicSans", 25, 500)
        y = 1660
        for l in ("Fotos: NASA (dominio público); P. Špindler (CC BY 3.0)",
                  "Música original, sin licencia de terceros · Análisis: Melina Rozas"):
            centrado(dib, y, l, f, SUAVE)
            y += 36

    def cuadro(self, seg):
        esc = self.t["escenas"]
        i = 0
        for k, e in enumerate(esc):
            if seg >= e["ini"]:
                i = k
        ini = 0.0 if i == 0 else esc[i]["ini"] - 0.2
        fin = esc[i + 1]["ini"] - 0.2 if i + 1 < len(esc) else self.t["duracion"]
        fn = getattr(self, esc[i]["id"])
        im = fn((seg - ini) / (fin - ini), seg - ini)
        if i + 1 < len(esc) and seg > fin - FUNDIDO:
            sig = getattr(self, esc[i + 1]["id"])(0, 0)
            im = Image.blend(im, sig, suave((seg - (fin - FUNDIDO)) / FUNDIDO))
        im = self.capas(im, seg)
        if i == len(esc) - 1:
            self.creditos_finales(ImageDraw.Draw(im, "RGBA"))
        return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provisional", action="store_true")
    ap.add_argument("--cuadros", help="segundos separados por coma: guarda esos cuadros en vez del video")
    ap.add_argument("--salida-cuadros", default=".")
    a = ap.parse_args()
    trabajo = AQUI / ".borrador" if a.provisional else AQUI
    tiempos = json.loads((trabajo / "tiempos.json").read_text(encoding="utf-8"))
    reel = Reel(tiempos, a.provisional)
    if a.cuadros:
        for s in a.cuadros.split(","):
            reel.cuadro(float(s)).save(Path(a.salida_cuadros) / f"cuadro_{float(s):05.1f}.png")
        return
    dur = tiempos["duracion"]
    salida = AQUI / ("reel_borrador.mp4" if a.provisional else "reel.mp4")
    fade = max(0, dur - 2.0)
    cmd = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ANCHO}x{ALTO}", "-r", str(FPS), "-i", "-",
           "-i", str(trabajo / "narracion.wav"), "-stream_loop", "-1", "-i", str(REC / "musica.flac"),
           "-filter_complex",
           f"[1:a]aresample=44100,aformat=channel_layouts=stereo[v];"
           f"[2:a]volume={MUSICA_GANANCIA},afade=t=in:d=1,afade=t=out:st={fade:.2f}:d=2,atrim=0:{dur:.2f}[m];"
           f"[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
           "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{dur:.2f}", str(salida)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(dur * FPS)
    for i in range(n):
        p.stdin.write(reel.cuadro(i / FPS).tobytes())
        if i % 300 == 0:
            print(f"{i}/{n}", flush=True)
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg falló")
    print(salida, f"{salida.stat().st_size / 1e6:.1f} MB, {dur:.1f} s")


if __name__ == "__main__":
    main()
