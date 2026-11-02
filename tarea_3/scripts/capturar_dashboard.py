"""Capturas del dashboard para el reel y LinkedIn, y prueba de sus controles en un navegador real.

Uso: python scripts/capturar_dashboard.py [URL]   (sin URL levanta un servidor local con web/)
Sale con error si algún control no cambia los resultados o si la consola registra errores.
"""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
REEL = RAIZ / "reel" / "recursos"
LINKEDIN = RAIZ / "linkedin"


def kpis(p):
    return [k.inner_text().replace("\n", " | ") for k in p.query_selector_all(".kpi")]


def elegir(p, selector, valor):
    p.select_option(selector, valor)
    p.wait_for_timeout(350)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
    srv = None
    if len(sys.argv) == 1:
        srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", str(RAIZ / "web")],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    errores, fallos = [], []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel="chrome", headless=True)
            ctx = b.new_context(viewport={"width": 1360, "height": 900}, color_scheme="light", accept_downloads=True)
            p = ctx.new_page()
            p.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
            p.on("pageerror", lambda e: errores.append(str(e)))
            p.goto(url)
            p.wait_for_function("window.__listo===true", timeout=20000)
            p.wait_for_timeout(400)
            base = kpis(p)
            print("Inicial:", *base, sep="\n  ")

            def probar(nombre, accion):
                antes = kpis(p)
                accion()
                despues = kpis(p)
                estado = "ok" if antes != despues else "SIN CAMBIO"
                print(f"{estado:10} {nombre}: {despues[0]} / {despues[2]}")
                if antes == despues:
                    fallos.append(nombre)

            probar("indicador = lluvia", lambda: elegir(p, "#f-ind", "lluvia_mm"))
            p.evaluate("scrollTo(0,0)")
            p.screenshot(path=LINKEDIN / "captura_lluvia.png", clip={"x": 0, "y": 0, "width": 1360, "height": 1500}, full_page=True)
            probar("indicador = t. máxima", lambda: elegir(p, "#f-ind", "temp_max"))
            elegir(p, "#f-ind", "temp_media")
            probar("desde = 2000", lambda: elegir(p, "#f-desde", "2000"))
            probar("hasta = 2015", lambda: elegir(p, "#f-hasta", "2015"))
            p.click("#f-limpiar"); p.wait_for_timeout(300)
            probar("temporada = jun-ago", lambda: elegir(p, "#f-temporada", "jun_ago"))
            p.click("#f-limpiar"); p.wait_for_timeout(300)
            probar("zona = Selva", lambda: elegir(p, "#f-zona", "Selva"))
            n_filas = len(p.query_selector_all("#tabla tbody tr"))
            print("filas de tabla con zona Selva:", n_filas)
            if n_filas != 5:
                fallos.append("tabla por zona")
            probar("departamento = Ucayali", lambda: elegir(p, "#f-dep", "Ucayali"))
            p.select_option("#f-comp", "Ica"); p.wait_for_timeout(300)
            print("leyenda con comparación:", p.inner_text("#linea-leyenda").replace("\n", " · "))
            p.click("#f-limpiar"); p.wait_for_timeout(300)
            # clic en el mapa
            p.locator("#mapa path[aria-label='Puno']").click(force=True); p.wait_for_timeout(300)
            print("clic en mapa →", p.input_value("#f-dep"))
            if p.input_value("#f-dep") != "Puno":
                fallos.append("clic en mapa")
            p.click("#f-limpiar"); p.wait_for_timeout(300)
            # búsqueda
            p.fill("#buscar", "huan"); p.wait_for_timeout(200)
            print("búsqueda 'huan':", p.inner_text("#tabla-nota"))
            if len(p.query_selector_all("#tabla tbody tr")) != 2:
                fallos.append("búsqueda")
            p.fill("#buscar", ""); p.wait_for_timeout(200)
            # descarga
            with p.expect_download() as d:
                p.click("#descargar")
            ruta = d.value.path()
            lineas = Path(ruta).read_text(encoding="utf-8-sig").splitlines()
            print("CSV:", d.value.suggested_filename, len(lineas) - 1, "filas")
            if len(lineas) - 1 != 25 * 45:
                fallos.append("descarga")
            # comprobación final: restablecer vuelve al estado inicial
            if kpis(p) != base:
                fallos.append("restablecer")

            p.evaluate("scrollTo(0,0)")
            p.wait_for_timeout(200)
            p.screenshot(path=LINKEDIN / "captura_tablero.png", clip={"x": 0, "y": 0, "width": 1360, "height": 1500}, full_page=True)
            p.locator("#hallazgos").scroll_into_view_if_needed()
            p.wait_for_timeout(300)
            p.locator("#hallazgos").screenshot(path=LINKEDIN / "captura_hallazgos.png")
            print("desborde horizontal escritorio:", p.evaluate("document.documentElement.scrollWidth-innerWidth"))

            p.click("#tema"); p.wait_for_timeout(300)
            print("tema:", p.evaluate("document.documentElement.dataset.theme"))
            p.evaluate("scrollTo(0,0)")
            p.screenshot(path=str(RAIZ / ".captura_oscuro.png"), full_page=True)
            ctx.close()

            # Vista de celular, para el reel
            ctx = b.new_context(viewport={"width": 420, "height": 860}, device_scale_factor=2.5, color_scheme="dark", is_mobile=True, has_touch=True)
            m = ctx.new_page()
            m.on("console", lambda x: errores.append(x.text) if x.type == "error" else None)
            m.on("pageerror", lambda e: errores.append(str(e)))
            m.goto(url)
            m.wait_for_function("window.__listo===true", timeout=20000)
            m.wait_for_timeout(500)
            print("desborde horizontal celular:", m.evaluate("document.documentElement.scrollWidth-innerWidth"))
            m.screenshot(path=REEL / "dashboard_1_temperatura.png", full_page=True)
            elegir(m, "#f-ind", "lluvia_mm")
            m.screenshot(path=REEL / "dashboard_2_lluvia.png", full_page=True)
            ctx.close()
            b.close()
    finally:
        if srv:
            srv.kill()
    if errores:
        fallos.append(f"consola: {errores}")
    if fallos:
        sys.exit(f"FALLÓ: {fallos}")
    print("Todas las pruebas pasaron.")


if __name__ == "__main__":
    main()
