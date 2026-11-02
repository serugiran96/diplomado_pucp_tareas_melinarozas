/* Dashboard de clima del Perú. Todos los indicadores se recalculan aquí desde los datos mensuales. */
const IND = {
  temp_media: { nombre: "Temperatura media", unidad: "°C", tipo: "temp" },
  temp_max: { nombre: "Temperatura máxima", unidad: "°C", tipo: "temp" },
  temp_min: { nombre: "Temperatura mínima", unidad: "°C", tipo: "temp" },
  lluvia_mm: { nombre: "Lluvia acumulada", unidad: "mm", tipo: "lluvia" },
};
const TEMPORADAS = {
  anual: { nombre: "todo el año", meses: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] },
  dic_feb: { nombre: "dic-feb", meses: [12, 1, 2] },
  mar_may: { nombre: "mar-may", meses: [3, 4, 5] },
  jun_ago: { nombre: "jun-ago", meses: [6, 7, 8] },
  sep_nov: { nombre: "sep-nov", meses: [9, 10, 11] },
};
const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
const BASE = [1991, 2020];
const estado = { ind: "temp_media", desde: 1981, hasta: 2025, temporada: "anual", zona: "Todas", dep: "", comp: "" };
let D, GEO, orden = { col: "tendencia", asc: false };

const $ = (s) => document.querySelector(s);
const num = (x, d = 2) => x.toLocaleString("es-PE", { minimumFractionDigits: d, maximumFractionDigits: d });
const signo = (x, d = 2) => (x > 0 ? "+" : x < 0 ? "−" : "") + num(Math.abs(x), d);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

/* ---------- Cálculo ---------- */
function anual(serie, ind, temporada) {
  const meses = TEMPORADAS[temporada].meses, v = serie[ind], salida = [];
  D.anios.forEach((a, i) => {
    const xs = meses.map((m) => v[i * 12 + m - 1]);
    const s = xs.reduce((p, c) => p + c, 0);
    salida.push({ anio: a, valor: IND[ind].tipo === "lluvia" ? s : s / xs.length });
  });
  return salida;
}
function tCritico(gl) {   // Cornish-Fisher para t de Student al 97.5 %
  const z = 1.959964;
  return z + (z ** 3 + z) / (4 * gl) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * gl ** 2);
}
function calcular(filas) {
  const n = filas.length, xm = d3.mean(filas, (d) => d.anio), ym = d3.mean(filas, (d) => d.valor);
  let sxx = 0, sxy = 0, sse = 0;
  filas.forEach((d) => { sxx += (d.anio - xm) ** 2; sxy += (d.anio - xm) * (d.valor - ym); });
  const b = sxy / sxx, a = ym - b * xm;
  filas.forEach((d) => { sse += (d.valor - (a + b * d.anio)) ** 2; });
  const ee = Math.sqrt(sse / (n - 2) / sxx), ic = tCritico(n - 2) * ee;
  const nv = Math.min(20, Math.floor(n / 2));
  const m1 = d3.mean(filas.slice(0, nv), (d) => d.valor), m2 = d3.mean(filas.slice(-nv), (d) => d.valor);
  return { b, a, media: ym, porDecada: b * 10, ic: ic * 10, m1, m2, nv, dif: m2 - m1, difPct: 100 * (m2 / m1 - 1),
    extremo: d3.greatest(filas, (d) => d.valor) };
}
const relativo = (e) => IND[estado.ind].tipo === "lluvia";
/* Tendencia en la unidad que se compara: °C/década en temperatura y %/década en lluvia. */
const tendencia = (e) => (relativo() ? (100 * e.porDecada) / e.media : e.porDecada);
const intervalo = (e) => (relativo() ? (100 * e.ic) / e.media : e.ic);
const cambio = (e) => (relativo() ? e.difPct : e.dif);
const uT = () => (relativo() ? "%" : "°C");

function deptosVisibles() {
  return D.departamentos.filter((d) => estado.zona === "Todas" || D.zona[d] === estado.zona);
}
function porPeriodo(filas) { return filas.filter((d) => d.anio >= estado.desde && d.anio <= estado.hasta); }
function serieDe(dep) { return porPeriodo(anual(D.serie[dep], estado.ind, estado.temporada)); }
function serieNacional() { return porPeriodo(anual(D.nacional, estado.ind, estado.temporada)); }
function serieZona(z) {
  const ds = D.departamentos.filter((d) => D.zona[d] === z).map(serieDe);
  return ds[0].map((f, i) => ({ anio: f.anio, valor: d3.mean(ds, (s) => s[i].valor) }));
}
function serieAlcance() {
  if (estado.dep) return { nombre: estado.dep, filas: serieDe(estado.dep) };
  if (estado.zona !== "Todas") return { nombre: `${estado.zona} (promedio de departamentos)`, filas: serieZona(estado.zona) };
  return { nombre: "Perú", filas: serieNacional() };
}
function tablaDeptos() {
  return deptosVisibles().map((d) => {
    const filas = serieDe(d), e = calcular(filas);
    return { dep: d, zona: D.zona[d], altitud: D.altitud[d], e, tendencia: tendencia(e), ic: intervalo(e), cambio: cambio(e), media: e.media };
  });
}
function spearman(xs, ys) {
  const rango = (v) => {
    const o = v.map((x, i) => [x, i]).sort((a, b) => a[0] - b[0]), r = Array(v.length);
    for (let i = 0; i < o.length;) {
      let j = i;
      while (j + 1 < o.length && o[j + 1][0] === o[i][0]) j++;
      for (let k = i; k <= j; k++) r[o[k][1]] = (i + j) / 2 + 1;
      i = j + 1;
    }
    return r;
  };
  const rx = rango(xs), ry = rango(ys), mx = d3.mean(rx), my = d3.mean(ry);
  let a = 0, b = 0, c = 0;
  rx.forEach((x, i) => { a += (x - mx) * (ry[i] - my); b += (x - mx) ** 2; c += (ry[i] - my) ** 2; });
  return a / Math.sqrt(b * c);
}

/* ---------- Color ---------- */
function divergente(max) {
  const lluvia = relativo();
  const frio = ["#104281", "#5598e7"];
  const calido = lluvia ? ["#d9914a", "#8a4a12"] : ["#ec7f72", "#9c1f1f"];
  const medio = css("--medio");
  const neg = lluvia ? d3.interpolateRgbBasis([medio, calido[0], calido[1]]) : d3.interpolateRgbBasis([medio, frio[1], frio[0]]);
  const pos = lluvia ? d3.interpolateRgbBasis([medio, frio[1], frio[0]]) : d3.interpolateRgbBasis([medio, calido[0], calido[1]]);
  const f = (v) => {
    const t = Math.min(1, Math.abs(v) / (max || 1));
    return v < 0 ? neg(t) : pos(t);
  };
  f.rampa = `linear-gradient(90deg, ${neg(1)}, ${neg(0.5)}, ${medio}, ${pos(0.5)}, ${pos(1)})`;
  return f;
}

/* ---------- Ayudas de SVG ---------- */
const ayuda = () => $("#ayuda");
function mostrarAyuda(ev, titulo, filas) {
  const a = ayuda();
  a.replaceChildren();
  const b = document.createElement("b"); b.textContent = titulo; a.append(b);
  filas.forEach((f) => {
    const div = document.createElement("div"); div.className = "fila";
    if (f.color) { const i = document.createElement("i"); i.style.background = f.color; div.append(i); }
    const v = document.createElement("strong"); v.textContent = f.valor; div.append(v);
    const s = document.createElement("span"); s.textContent = f.rotulo; div.append(s);
    a.append(div);
  });
  a.style.display = "block";
  const r = a.getBoundingClientRect();
  let x = (ev.clientX ?? 0) + 14, y = (ev.clientY ?? 0) + 14;
  if (x + r.width > innerWidth - 8) x = (ev.clientX ?? 0) - r.width - 14;
  if (y + r.height > innerHeight - 8) y = (ev.clientY ?? 0) - r.height - 14;
  a.style.left = `${Math.max(8, x)}px`; a.style.top = `${Math.max(8, y)}px`;
}
const ocultarAyuda = () => { ayuda().style.display = "none"; };
function lienzo(id, alto) {
  const caja = $(id); caja.replaceChildren();
  const ancho = Math.max(280, caja.clientWidth);
  const svg = d3.select(caja).append("svg").attr("viewBox", `0 0 ${ancho} ${alto}`).attr("role", "img");
  return { svg, ancho, alto };
}
function focoAyuda(sel, fn) {
  sel.attr("tabindex", 0)
    .on("pointermove", (ev, d) => fn(ev, d))
    .on("pointerleave blur", ocultarAyuda)
    .on("focus", function (ev, d) {
      const r = this.getBoundingClientRect();
      fn({ clientX: r.right, clientY: r.top }, d);
    });
}
function elegirDep(d) {
  estado.dep = estado.dep === d ? "" : d;
  if (estado.comp === estado.dep) estado.comp = "";
  sincronizar(); dibujar();
}

/* ---------- Gráficos ---------- */
function dibujarMapa(tabla) {
  const { svg, ancho, alto } = lienzo("#mapa", Math.min(620, Math.max(400, $("#mapa").clientWidth * 1.3)));
  const proy = d3.geoIdentity().reflectY(true).fitExtent([[6, 6], [ancho - 6, alto - 6]], GEO);
  const camino = d3.geoPath(proy);
  const porDep = new Map(tabla.map((f) => [f.dep, f]));
  const todos = D.departamentos.map((d) => { const e = calcular(serieDe(d)); return tendencia(e); });
  const max = d3.max(todos, Math.abs);
  const color = divergente(max);
  svg.attr("aria-label", "Mapa de departamentos del Perú coloreado por tendencia");
  const sel = svg.selectAll("path").data(GEO.features).join("path")
    .attr("class", (f) => `dep${porDep.has(f.properties.nombre) ? "" : " apagado"}${f.properties.nombre === estado.dep ? " activo" : ""}`)
    .attr("d", camino)
    .attr("fill", (f) => color(tendencia(calcular(serieDe(f.properties.nombre)))))
    .attr("aria-label", (f) => f.properties.nombre)
    .on("click", (_, f) => elegirDep(f.properties.nombre))
    .on("keydown", (ev, f) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); elegirDep(f.properties.nombre); } });
  focoAyuda(sel, (ev, f) => {
    const e = calcular(serieDe(f.properties.nombre));
    mostrarAyuda(ev, f.properties.nombre, [
      { valor: `${signo(tendencia(e))} ${uT()}`, rotulo: "por década" },
      { valor: `${signo(cambio(e), relativo() ? 1 : 2)} ${uT()}`, rotulo: `últimos ${e.nv} vs primeros ${e.nv} años` },
    ]);
  });
  sel.filter((f) => f.properties.nombre === estado.dep).raise();
  $("#mapa-escala").replaceChildren();
  const esc = $("#mapa-escala");
  const izq = document.createElement("span"); izq.textContent = `${signo(-max)} ${uT()}`;
  const barra = document.createElement("div"); barra.className = "barra"; barra.style.background = color.rampa;
  const der = document.createElement("span"); der.textContent = `${signo(max)} ${uT()} por década`;
  esc.append(izq, barra, der);
}

function dibujarLinea() {
  const al = serieAlcance(), hay = !!estado.dep || estado.zona !== "Todas";
  const series = [];
  if (hay) series.push({ nombre: "Perú", filas: serieNacional(), color: css("--tinta-3"), ancho: 1.5 });
  series.push({ nombre: al.nombre.replace(" (promedio de departamentos)", ""), filas: al.filas, color: css("--serie-1"), ancho: 2, principal: true });
  if (estado.comp) series.push({ nombre: estado.comp, filas: serieDe(estado.comp), color: css("--serie-2"), ancho: 2 });
  const ley = $("#linea-leyenda"); ley.replaceChildren();
  series.forEach((s) => {
    const sp = document.createElement("span"), i = document.createElement("i");
    i.style.background = s.color; sp.append(i, document.createTextNode(s.nombre)); ley.append(sp);
  });
  const sp = document.createElement("span"), i = document.createElement("i");
  i.style.background = css("--serie-1"); i.style.opacity = 0.45;
  sp.append(i, document.createTextNode(`Tendencia lineal de ${series.find((s) => s.principal).nombre}`)); ley.append(sp);

  const { svg, ancho, alto } = lienzo("#linea", 340);
  const m = { t: 10, r: 14, b: 26, l: 46 };
  const x = d3.scaleLinear().domain([estado.desde, estado.hasta]).range([m.l, ancho - m.r]);
  const y = d3.scaleLinear().domain(d3.extent(series.flatMap((s) => s.filas), (d) => d.valor)).nice().range([alto - m.b, m.t]);
  svg.attr("aria-label", `Serie anual de ${IND[estado.ind].nombre}`);
  svg.append("g").attr("class", "reja").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(ancho - m.l - m.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b})`).call(d3.axisBottom(x).ticks(ancho < 460 ? 5 : 9).tickFormat(d3.format("d")).tickSizeOuter(0));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(0)).select(".domain").remove();
  const linea = d3.line().x((d) => x(d.anio)).y((d) => y(d.valor));
  const ppal = series.find((s) => s.principal), e = calcular(ppal.filas);
  svg.append("line").attr("x1", x(estado.desde)).attr("x2", x(estado.hasta)).attr("y1", y(e.a + e.b * estado.desde)).attr("y2", y(e.a + e.b * estado.hasta))
    .attr("stroke", ppal.color).attr("stroke-width", 1.5).attr("opacity", 0.45);
  series.forEach((s) => {
    svg.append("path").datum(s.filas).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", s.ancho)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round").attr("d", linea);
  });
  const fin = ppal.filas[ppal.filas.length - 1];
  svg.append("circle").attr("cx", x(fin.anio)).attr("cy", y(fin.valor)).attr("r", 4).attr("fill", ppal.color).attr("stroke", css("--superficie")).attr("stroke-width", 2);
  const guia = svg.append("line").attr("y1", m.t).attr("y2", alto - m.b).attr("stroke", css("--eje")).style("display", "none");
  svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", ancho - m.l - m.r).attr("height", alto - m.t - m.b).attr("fill", "transparent")
    .on("pointermove", (ev) => {
      const [px] = d3.pointer(ev), anio = Math.max(estado.desde, Math.min(estado.hasta, Math.round(x.invert(px))));
      guia.style("display", null).attr("x1", x(anio)).attr("x2", x(anio));
      mostrarAyuda(ev, String(anio), series.map((s) => ({ color: s.color, valor: `${num(s.filas.find((f) => f.anio === anio).valor, relativo() ? 0 : 2)} ${IND[estado.ind].unidad}`, rotulo: s.nombre })));
    })
    .on("pointerleave", () => { guia.style("display", "none"); ocultarAyuda(); });
}

function dibujarRanking(tabla) {
  const filas = [...tabla].sort((a, b) => b.tendencia - a.tendencia);
  const fila = 22, m = { t: 8, r: 58, b: 26, l: 104 };
  const { svg, ancho, alto } = lienzo("#ranking", m.t + m.b + filas.length * fila);
  const min = d3.min(filas, (f) => f.tendencia - f.ic), max = d3.max(filas, (f) => f.tendencia + f.ic);
  const x = d3.scaleLinear().domain([Math.min(0, min), Math.max(0, max)]).nice().range([m.l, ancho - m.r]);
  const y = (i) => m.t + i * fila + fila / 2;
  svg.attr("aria-label", "Ranking de departamentos por tendencia con intervalo de confianza");
  svg.append("g").attr("class", "reja").attr("transform", `translate(0,${m.t})`).call(d3.axisBottom(x).ticks(5).tickSize(alto - m.t - m.b).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b})`).call(d3.axisBottom(x).ticks(5).tickSizeOuter(0).tickFormat((v) => `${signo(v, relativo() ? 0 : 1)}`));
  svg.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", m.t).attr("y2", alto - m.b).attr("stroke", css("--tinta-3"));
  const g = svg.selectAll("g.f").data(filas).join("g").attr("class", "f").style("cursor", "pointer")
    .attr("transform", (_, i) => `translate(0,${y(i)})`)
    .attr("aria-label", (f) => `${f.dep}: ${signo(f.tendencia)} ${uT()} por década`)
    .on("click", (_, f) => elegirDep(f.dep))
    .on("keydown", (ev, f) => { if (ev.key === "Enter") elegirDep(f.dep); });
  g.append("rect").attr("x", 0).attr("y", -fila / 2).attr("width", ancho).attr("height", fila).attr("fill", (f) => (f.dep === estado.dep ? css("--lavado") : "transparent"));
  g.append("text").attr("x", m.l - 8).attr("dy", "0.32em").attr("text-anchor", "end").attr("class", "etiqueta").attr("font-weight", (f) => (f.dep === estado.dep ? 650 : 400)).text((f) => f.dep);
  g.append("line").attr("x1", (f) => x(f.tendencia - f.ic)).attr("x2", (f) => x(f.tendencia + f.ic)).attr("stroke", css("--serie-1")).attr("stroke-width", 2).attr("stroke-linecap", "round").attr("opacity", 0.35);
  g.append("circle").attr("cx", (f) => x(f.tendencia)).attr("r", 4.5).attr("fill", css("--serie-1")).attr("stroke", css("--superficie")).attr("stroke-width", 2);
  g.append("text").attr("x", ancho - 2).attr("dy", "0.32em").attr("text-anchor", "end").attr("class", "etiqueta-2").style("font-variant-numeric", "tabular-nums").text((f) => signo(f.tendencia, relativo() ? 1 : 2));
  focoAyuda(g, (ev, f) => mostrarAyuda(ev, f.dep, [
    { valor: `${signo(f.tendencia)} ${uT()}`, rotulo: "por década" },
    { valor: `± ${num(f.ic)}`, rotulo: "IC 95 %" },
  ]));
}

function dibujarFranjas() {
  const zonas = ["Costa", "Sierra", "Selva"].filter((z) => estado.zona === "Todas" || z === estado.zona);
  const filasZ = zonas.flatMap((z) => D.departamentos.filter((d) => D.zona[d] === z).map((d) => ({ dep: d, zona: z })));
  const celda = 19, sep = 14, m = { t: 6, r: 8, b: 24, l: 104 };
  const alto = m.t + m.b + filasZ.length * celda + (zonas.length - 1) * sep;
  const { svg, ancho } = lienzo("#franjas-depto", alto);
  const anios = d3.range(estado.desde, estado.hasta + 1);
  const x = d3.scaleBand().domain(anios).range([m.l, ancho - m.r]);
  const lluvia = relativo();
  const datos = filasZ.map((f) => {
    const filas = anual(D.serie[f.dep], estado.ind, estado.temporada);
    const base = d3.mean(filas.filter((d) => d.anio >= BASE[0] && d.anio <= BASE[1]), (d) => d.valor);
    return { ...f, filas: filas.filter((d) => d.anio >= estado.desde && d.anio <= estado.hasta).map((d) => ({ anio: d.anio, valor: d.valor, anom: lluvia ? (100 * (d.valor - base)) / base : d.valor - base })) };
  });
  const max = d3.quantile(datos.flatMap((d) => d.filas.map((c) => Math.abs(c.anom))).sort(d3.ascending), 0.98);
  const color = divergente(max);
  svg.attr("aria-label", "Mapa de calor de anomalías por departamento y año");
  let y = m.t, zonaActual = zonas[0];
  datos.forEach((f) => {
    if (f.zona !== zonaActual) { y += sep; zonaActual = f.zona; }
    const g = svg.append("g").attr("transform", `translate(0,${y})`);
    g.append("text").attr("x", m.l - 8).attr("y", celda / 2).attr("dy", "0.32em").attr("text-anchor", "end").attr("class", "etiqueta").attr("font-weight", f.dep === estado.dep ? 650 : 400).style("cursor", "pointer").text(f.dep).on("click", () => elegirDep(f.dep));
    const r = g.selectAll("rect").data(f.filas).join("rect").attr("class", "celda")
      .attr("x", (c) => x(c.anio)).attr("width", Math.max(1, x.bandwidth() - 1)).attr("height", celda - 2).attr("rx", 1)
      .attr("fill", (c) => color(c.anom)).on("click", () => elegirDep(f.dep));
    r.on("pointermove", (ev, c) => mostrarAyuda(ev, `${f.dep}, ${c.anio}`, [
      { valor: `${signo(c.anom, lluvia ? 0 : 2)} ${lluvia ? "%" : "°C"}`, rotulo: "anomalía" },
      { valor: `${num(c.valor, lluvia ? 0 : 2)} ${IND[estado.ind].unidad}`, rotulo: "valor" },
    ])).on("pointerleave", ocultarAyuda);
    y += celda;
  });
  const paso = Math.ceil(anios.length / (ancho < 560 ? 5 : 10));
  const eje = d3.axisBottom(x).tickValues(anios.filter((a, i) => i % paso === 0)).tickFormat(d3.format("d")).tickSize(0);
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b + 2})`).call(eje).select(".domain").remove();
  const esc = $("#franjas-escala"); esc.replaceChildren();
  const a = document.createElement("span"); a.textContent = `${signo(-max, lluvia ? 0 : 1)} ${lluvia ? "%" : "°C"}`;
  const b = document.createElement("div"); b.className = "barra"; b.style.background = color.rampa;
  const c = document.createElement("span"); c.textContent = `${signo(max, lluvia ? 0 : 1)} ${lluvia ? "%" : "°C"} frente a 1991-2020`;
  esc.append(a, b, c);
}

function dibujarEstacional() {
  const serie = estado.dep ? D.serie[estado.dep] : D.nacional, lluvia = relativo();
  const al = serieAlcance().filas, nv = Math.min(20, Math.floor(al.length / 2));
  const a1 = [estado.desde, estado.desde + nv - 1], a2 = [estado.hasta - nv + 1, estado.hasta];
  const prom = (r) => MESES.map((_, m) => {
    const xs = [];
    D.anios.forEach((a, i) => { if (a >= r[0] && a <= r[1]) xs.push(serie[estado.ind][i * 12 + m]); });
    return { mes: m, valor: d3.mean(xs) };
  });
  const s1 = prom(a1), s2 = prom(a2);
  const c1 = css("--tinta-3"), c2 = css("--serie-1");
  const ley = $("#estacional-leyenda"); ley.replaceChildren();
  [[`${a1[0]}-${a1[1]}`, c1], [`${a2[0]}-${a2[1]}`, c2]].forEach(([t, c]) => {
    const sp = document.createElement("span"), i = document.createElement("i");
    i.style.background = c; sp.append(i, document.createTextNode(t)); ley.append(sp);
  });
  const { svg, ancho, alto } = lienzo("#estacional", 300);
  const m = { t: 10, r: 12, b: 24, l: 42 };
  const x = d3.scalePoint().domain(d3.range(12)).range([m.l, ancho - m.r]);
  const y = d3.scaleLinear().domain(d3.extent([...s1, ...s2], (d) => d.valor)).nice().range([alto - m.b, m.t]);
  svg.attr("aria-label", "Ciclo anual por mes en dos periodos");
  const elegidos = TEMPORADAS[estado.temporada].meses;
  if (estado.temporada !== "anual") elegidos.forEach((mes) => {
    const paso = x.step();
    svg.append("rect").attr("x", x(mes - 1) - paso / 2).attr("width", paso).attr("y", m.t).attr("height", alto - m.t - m.b).attr("fill", css("--lavado"));
  });
  svg.append("g").attr("class", "reja").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(ancho - m.l - m.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b})`).call(d3.axisBottom(x).tickFormat((i) => (ancho < 420 ? MESES[i][0] : MESES[i])).tickSizeOuter(0));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(0)).select(".domain").remove();
  const l = d3.line().x((d) => x(d.mes)).y((d) => y(d.valor));
  [[s1, c1, 1.5], [s2, c2, 2]].forEach(([s, c, w]) => svg.append("path").datum(s).attr("fill", "none").attr("stroke", c).attr("stroke-width", w).attr("stroke-linecap", "round").attr("d", l));
  const guia = svg.append("line").attr("y1", m.t).attr("y2", alto - m.b).attr("stroke", css("--eje")).style("display", "none");
  svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", ancho - m.l - m.r).attr("height", alto - m.t - m.b).attr("fill", "transparent")
    .on("pointermove", (ev) => {
      const [px] = d3.pointer(ev), i = Math.max(0, Math.min(11, Math.round((px - m.l) / x.step())));
      guia.style("display", null).attr("x1", x(i)).attr("x2", x(i));
      const u = IND[estado.ind].unidad, d = lluvia ? 0 : 2;
      mostrarAyuda(ev, MESES[i], [{ color: c2, valor: `${num(s2[i].valor, d)} ${u}`, rotulo: `${a2[0]}-${a2[1]}` }, { color: c1, valor: `${num(s1[i].valor, d)} ${u}`, rotulo: `${a1[0]}-${a1[1]}` }]);
    })
    .on("pointerleave", () => { guia.style("display", "none"); ocultarAyuda(); });
}

function dibujarZonas() {
  const filas = ["Costa", "Sierra", "Selva"].map((z) => {
    const e = calcular(serieZona(z));
    return { zona: z, valor: tendencia(e), cambio: cambio(e) };
  });
  const max = d3.max(filas, (f) => Math.abs(f.valor)) || 1;
  const caja = $("#zonas"); caja.replaceChildren();
  filas.forEach((f) => {
    const fila = document.createElement("button");
    fila.type = "button"; fila.className = "zona-fila" + (estado.zona === f.zona ? " activa" : "");
    fila.setAttribute("aria-pressed", estado.zona === f.zona);
    const n = document.createElement("span"); n.textContent = f.zona;
    const pista = document.createElement("span"); pista.className = "zona-pista";
    const barra = document.createElement("i"); barra.style.width = `${(100 * Math.abs(f.valor)) / max}%`;
    barra.style.background = f.valor < 0 ? css("--tinta-3") : css("--serie-1");
    pista.append(barra);
    const v = document.createElement("strong"); v.textContent = `${signo(f.valor)} ${uT()}`;
    fila.append(n, pista, v);
    fila.onclick = () => { estado.zona = estado.zona === f.zona ? "Todas" : f.zona; sincronizar(); dibujar(); };
    caja.append(fila);
  });
}

function dibujarDispersion(tabla) {
  const colores = { Costa: css("--serie-1"), Sierra: css("--serie-2"), Selva: css("--serie-3") };
  const formas = { Costa: d3.symbolCircle, Sierra: d3.symbolSquare, Selva: d3.symbolTriangle };
  const ley = $("#dispersion-leyenda"); ley.replaceChildren();
  ["Costa", "Sierra", "Selva"].filter((z) => tabla.some((f) => f.zona === z)).forEach((z) => {
    const sp = document.createElement("span"), i = document.createElement("i");
    i.className = z === "Costa" ? "pto" : z === "Sierra" ? "cua" : "tri";
    if (z === "Selva") i.style.borderBottomColor = colores[z]; else i.style.background = colores[z];
    sp.append(i, document.createTextNode(z)); ley.append(sp);
  });
  const rho = spearman(tabla.map((f) => f.altitud), tabla.map((f) => f.tendencia));
  const sp = document.createElement("span"); sp.textContent = `Correlación de Spearman: ${signo(rho)}`; ley.append(sp);
  const { svg, ancho, alto } = lienzo("#dispersion", 250);
  const m = { t: 12, r: 14, b: 40, l: 46 };
  const x = d3.scaleLinear().domain([0, 4000]).range([m.l, ancho - m.r]);
  const y = d3.scaleLinear().domain(d3.extent(tabla, (f) => f.tendencia)).nice().range([alto - m.b, m.t]);
  svg.attr("aria-label", "Altitud media frente a tendencia por departamento");
  svg.append("g").attr("class", "reja").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(ancho - m.l - m.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b})`).call(d3.axisBottom(x).ticks(5).tickFormat(d3.format("d")).tickSizeOuter(0));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(0)).select(".domain").remove();
  svg.append("text").attr("x", ancho - m.r).attr("y", alto - 6).attr("text-anchor", "end").attr("class", "etiqueta-2").text("Altitud media de la celda (m)");
  svg.selectAll("path.p").data(tabla).join("path").attr("class", "p").style("cursor", "pointer")
    .attr("transform", (f) => `translate(${x(f.altitud)},${y(f.tendencia)})`)
    .attr("d", (f) => d3.symbol(formas[f.zona], f.dep === estado.dep ? 170 : 80)())
    .attr("fill", (f) => colores[f.zona]).attr("stroke", css("--superficie")).attr("stroke-width", 2);
  const etiquetas = new Set([estado.dep, estado.comp, ...[...tabla].sort((a, b) => b.tendencia - a.tendencia).slice(0, 1).map((f) => f.dep), ...[...tabla].sort((a, b) => a.tendencia - b.tendencia).slice(0, 1).map((f) => f.dep)]);
  tabla.filter((f) => etiquetas.has(f.dep)).forEach((f) => {
    const der = x(f.altitud) < ancho - 110;
    svg.append("text").attr("x", x(f.altitud) + (der ? 9 : -9)).attr("y", y(f.tendencia)).attr("dy", "0.32em").attr("text-anchor", der ? "start" : "end").attr("class", "etiqueta").text(f.dep);
  });
  const delaunay = d3.Delaunay.from(tabla, (f) => x(f.altitud), (f) => y(f.tendencia));
  svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", ancho - m.l - m.r).attr("height", alto - m.t - m.b).attr("fill", "transparent").style("cursor", "pointer")
    .on("pointermove", (ev) => {
      const [px, py] = d3.pointer(ev), f = tabla[delaunay.find(px, py)];
      mostrarAyuda(ev, f.dep, [{ valor: `${signo(f.tendencia)} ${uT()}`, rotulo: "por década" }, { valor: `${num(f.altitud, 0)} m`, rotulo: "altitud media" }]);
    })
    .on("pointerleave", ocultarAyuda)
    .on("click", (ev) => { const [px, py] = d3.pointer(ev); elegirDep(tabla[delaunay.find(px, py)].dep); });
}

/* NASA POWER y ERA5 en el mismo punto, siempre 1981-2025: este contraste se calcula aparte en Python. */
function dibujarContraste() {
  const lluvia = relativo(), er = D.resultados.era5, u = lluvia ? "%" : "°C";
  const filas = (lluvia ? er.lluvia : er.temp).map((f) => ({ dep: f.departamento,
    nasa: lluvia ? f.cambio_nasa_celda_pct : f.tend_nasa_celda, era5: lluvia ? f.cambio_era5_pct : f.tend_era5 }))
    .filter((f) => estado.zona === "Todas" || D.zona[f.dep] === estado.zona);
  $("#titulo-contraste").textContent = lluvia ? "¿Coinciden las fuentes en la lluvia?" : "¿Coinciden las fuentes en la temperatura?";
  $("#sub-contraste").textContent = lluvia
    ? "Cambio 2006-2025 frente a 1981-2000 (%), todo el año. Sobre la diagonal, las dos fuentes dirían lo mismo. No cambia con los filtros de periodo."
    : "Tendencia de la temperatura media 1981-2025 (°C por década). Sobre la diagonal, las dos fuentes dirían lo mismo. No cambia con los filtros de periodo.";
  const { svg, ancho, alto } = lienzo("#contraste", 300);
  const m = { t: 12, r: 14, b: 40, l: 46 };
  const ext = d3.extent(filas.flatMap((f) => [f.nasa, f.era5, 0]));
  const x = d3.scaleLinear().domain(ext).nice().range([m.l, ancho - m.r]);
  const y = d3.scaleLinear().domain(ext).nice().range([alto - m.b, m.t]);
  svg.attr("aria-label", "NASA POWER frente a ERA5 por departamento");
  svg.append("g").attr("class", "reja").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(ancho - m.l - m.r)).tickFormat(""));
  svg.append("g").attr("class", "eje").attr("transform", `translate(0,${alto - m.b})`).call(d3.axisBottom(x).ticks(5).tickSizeOuter(0));
  svg.append("g").attr("class", "eje").attr("transform", `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(0)).select(".domain").remove();
  const [a, b] = x.domain();
  svg.append("line").attr("x1", x(a)).attr("y1", y(a)).attr("x2", x(b)).attr("y2", y(b)).attr("stroke", css("--tinta-3"));
  svg.append("text").attr("x", ancho - m.r).attr("y", alto - 6).attr("text-anchor", "end").attr("class", "etiqueta-2").text(`NASA POWER (${u})`);
  svg.append("text").attr("x", 4).attr("y", m.t - 2).attr("class", "etiqueta-2").text(`ERA5 (${u})`);
  svg.selectAll("circle.p").data(filas).join("circle").attr("cx", (f) => x(f.nasa)).attr("cy", (f) => y(f.era5))
    .attr("r", (f) => (f.dep === estado.dep ? 7 : 4.5)).attr("fill", css("--serie-1")).attr("stroke", css("--superficie")).attr("stroke-width", 2);
  const etiquetas = new Set([estado.dep, ...[...filas].sort((p, q) => Math.abs(q.nasa - q.era5) - Math.abs(p.nasa - p.era5)).slice(0, 2).map((f) => f.dep)]);
  filas.filter((f) => etiquetas.has(f.dep)).forEach((f) => {
    const der = x(f.nasa) < ancho - 110;
    svg.append("text").attr("x", x(f.nasa) + (der ? 9 : -9)).attr("y", y(f.era5)).attr("dy", "0.32em").attr("text-anchor", der ? "start" : "end").attr("class", "etiqueta").text(f.dep);
  });
  const delaunay = d3.Delaunay.from(filas, (f) => x(f.nasa), (f) => y(f.era5));
  svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", ancho - m.l - m.r).attr("height", alto - m.t - m.b).attr("fill", "transparent").style("cursor", "pointer")
    .on("pointermove", (ev) => {
      const [px, py] = d3.pointer(ev), f = filas[delaunay.find(px, py)], d = lluvia ? 1 : 2;
      mostrarAyuda(ev, f.dep, [{ valor: `${signo(f.nasa, d)} ${u}`, rotulo: "NASA POWER" }, { valor: `${signo(f.era5, d)} ${u}`, rotulo: "ERA5" }]);
    })
    .on("pointerleave", ocultarAyuda)
    .on("click", (ev) => { const [px, py] = d3.pointer(ev); elegirDep(filas[delaunay.find(px, py)].dep); });
}

function dibujarTabla(tabla) {
  const q = $("#buscar").value.trim().toLowerCase().normalize("NFD").replace(/\p{M}/gu, "");
  const u = IND[estado.ind].unidad, lluvia = relativo();
  const cols = [
    ["dep", "Departamento", (f) => f.dep], ["zona", "Zona", (f) => f.zona],
    ["altitud", "Altitud (m)", (f) => num(f.altitud, 0)], ["media", `Media (${u})`, (f) => num(f.media, lluvia ? 0 : 2)],
    ["tendencia", `Tendencia (${uT()}/década)`, (f) => signo(f.tendencia)], ["ic", "IC 95 % (±)", (f) => num(f.ic)],
    ["cambio", `Cambio (${uT()})`, (f) => signo(f.cambio, lluvia ? 1 : 2)],
  ];
  const filas = tabla.filter((f) => f.dep.toLowerCase().normalize("NFD").replace(/\p{M}/gu, "").includes(q))
    .sort((a, b) => {
      const v = typeof a[orden.col] === "string" ? a[orden.col].localeCompare(b[orden.col], "es") : a[orden.col] - b[orden.col];
      return orden.asc ? v : -v;
    });
  const cab = $("#tabla thead"), cue = $("#tabla tbody");
  cab.replaceChildren(); cue.replaceChildren();
  const tr = document.createElement("tr");
  cols.forEach(([k, t]) => {
    const th = document.createElement("th"); th.textContent = t + (orden.col === k ? (orden.asc ? " ↑" : " ↓") : ""); th.scope = "col";
    th.onclick = () => { orden = { col: k, asc: orden.col === k ? !orden.asc : false }; dibujarTabla(tablaDeptos()); };
    tr.append(th);
  });
  cab.append(tr);
  filas.forEach((f) => {
    const r = document.createElement("tr"); r.onclick = () => elegirDep(f.dep);
    if (f.dep === estado.dep) r.className = "activa";
    cols.forEach(([, , fn]) => { const td = document.createElement("td"); td.textContent = fn(f); r.append(td); });
    cue.append(r);
  });
  $("#tabla-nota").textContent = `${filas.length} de ${tabla.length} departamentos`;
}

function dibujarKpis(tabla) {
  const al = serieAlcance(), e = calcular(al.filas), lluvia = relativo(), u = uT(), ini = estado.desde, fin = estado.hasta;
  const pos = tabla.filter((f) => f.tendencia > 0).length, top = d3.greatest(tabla, (f) => f.tendencia);
  const n = tabla.length * al.filas.length * TEMPORADAS[estado.temporada].meses.length;
  const kpis = [
    ["Tendencia", `${signo(tendencia(e), 2)} ${u}`, `por década · IC 95 %: ±${num(intervalo(e))}`],
    [`Últimos ${e.nv} vs primeros ${e.nv} años`, `${signo(cambio(e), lluvia ? 1 : 2)} ${u}`, `${ini}-${ini + e.nv - 1} frente a ${fin - e.nv + 1}-${fin}`],
    ["Mayor tendencia", top.dep, `${signo(top.tendencia)} ${u} por década`],
    [lluvia ? "Año más lluvioso" : "Año más cálido", String(e.extremo.anio), `${num(e.extremo.valor, lluvia ? 0 : 2)} ${IND[estado.ind].unidad} · ${al.nombre.replace(" (promedio de departamentos)", "")}`],
    ["Departamentos con aumento", `${pos} de ${tabla.length}`, lluvia ? "tendencia positiva de lluvia" : "tendencia positiva de temperatura"],
    ["Observaciones usadas", num(n, 0), "departamento × mes"],
  ];
  const caja = $("#kpis"); caja.replaceChildren();
  kpis.forEach(([r, v, nt]) => {
    const d = document.createElement("div"); d.className = "kpi";
    const a = document.createElement("div"); a.className = "rotulo"; a.textContent = r;
    const b = document.createElement("div"); b.className = "valor"; b.textContent = v;
    const c = document.createElement("div"); c.className = "nota"; c.textContent = nt;
    d.append(a, b, c); caja.append(d);
  });
  const nombre = IND[estado.ind].nombre.toLowerCase(), temp = TEMPORADAS[estado.temporada].nombre;
  const alc = $("#alcance"); alc.replaceChildren();
  const s = document.createElement("strong"); s.textContent = al.nombre;
  alc.append(document.createTextNode("Mostrando: "), s, document.createTextNode(` · ${nombre} · ${temp} · ${ini}-${fin}`));
  const tituloMapa = lluvia ? "Dónde cambió la lluvia" : "Dónde cambió la temperatura";
  $("#titulo-mapa").textContent = tituloMapa;
  $("#sub-mapa").textContent = `Tendencia ${ini}-${fin} (${u} por década). Haz clic en un departamento para seleccionarlo.`;
  $("#titulo-linea").textContent = `${IND[estado.ind].nombre} anual, ${ini}-${fin}`;
  $("#sub-linea").textContent = `${IND[estado.ind].unidad} · ${temp}. Pasa el cursor para leer cada año.`;
  $("#sub-ranking").textContent = `${u} por década, de mayor a menor. La barra clara es el intervalo de confianza al 95 %.`;
  $("#sub-franjas").textContent = `Diferencia de cada año frente a la normal 1991-2020 de ese departamento (${lluvia ? "%" : "°C"}).`;
  $("#sub-estacional").textContent = `${al.nombre.replace(" (promedio de departamentos)", "") === "Perú" || estado.dep ? (estado.dep || "Perú") : "Perú"}: promedio por mes (${IND[estado.ind].unidad}). Muestra los 12 meses; la temporada elegida se sombrea.`;
  $("#sub-dispersion").textContent = `Cada punto es un departamento. ¿Se calienta más lo que está más alto?`;
}

function dibujar() {
  const tabla = tablaDeptos();
  $("#aviso-lluvia").hidden = !relativo();
  dibujarKpis(tabla); dibujarMapa(tabla); dibujarLinea(); dibujarRanking(tabla);
  dibujarZonas(); dibujarFranjas(); dibujarEstacional(); dibujarDispersion(tabla); dibujarContraste(); dibujarTabla(tabla);
}

/* ---------- Controles ---------- */
function opciones(sel, lista, valor) {
  sel.replaceChildren();
  lista.forEach(([v, t]) => { const o = document.createElement("option"); o.value = v; o.textContent = t; sel.append(o); });
  sel.value = valor;
}
function sincronizar() {
  const vis = deptosVisibles();
  if (estado.dep && !vis.includes(estado.dep)) estado.dep = "";
  opciones($("#f-dep"), [["", estado.zona === "Todas" ? "Perú (nacional)" : `Toda la zona ${estado.zona}`], ...vis.map((d) => [d, d])], estado.dep);
  opciones($("#f-comp"), [["", "Ninguno"], ...D.departamentos.filter((d) => d !== estado.dep).map((d) => [d, d])], estado.comp);
  opciones($("#f-desde"), D.anios.filter((a) => a <= estado.hasta - 9).map((a) => [a, a]), estado.desde);
  opciones($("#f-hasta"), D.anios.filter((a) => a >= estado.desde + 9).map((a) => [a, a]), estado.hasta);
  $("#f-ind").value = estado.ind; $("#f-temporada").value = estado.temporada; $("#f-zona").value = estado.zona;
}
function descargar() {
  const deps = deptosVisibles();
  const filas = [["departamento", "zona", "anio", "temporada", "indicador", "valor", "unidad"].join(",")];
  deps.forEach((d) => serieDe(d).forEach((f) => filas.push([`"${d}"`, D.zona[d], f.anio, estado.temporada, estado.ind, f.valor.toFixed(3), IND[estado.ind].unidad].join(","))));
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["﻿" + filas.join("\n")], { type: "text/csv;charset=utf-8" }));
  a.download = `clima_peru_${estado.ind}_${estado.desde}_${estado.hasta}.csv`;
  a.click(); URL.revokeObjectURL(a.href);
}
function iniciarControles() {
  opciones($("#f-ind"), Object.entries(IND).map(([k, v]) => [k, v.nombre]), estado.ind);
  opciones($("#f-temporada"), [["anual", "Todo el año"], ["dic_feb", "Dic-feb"], ["mar_may", "Mar-may"], ["jun_ago", "Jun-ago"], ["sep_nov", "Sep-nov"]], estado.temporada);
  opciones($("#f-zona"), [["Todas", "Todas"], ["Costa", "Costa"], ["Sierra", "Sierra"], ["Selva", "Selva"]], estado.zona);
  const enlaza = (id, k, fn = (x) => x) => $(id).addEventListener("change", (ev) => { estado[k] = fn(ev.target.value); sincronizar(); dibujar(); });
  enlaza("#f-ind", "ind"); enlaza("#f-desde", "desde", Number); enlaza("#f-hasta", "hasta", Number);
  enlaza("#f-temporada", "temporada"); enlaza("#f-zona", "zona"); enlaza("#f-dep", "dep"); enlaza("#f-comp", "comp");
  $("#f-limpiar").onclick = () => { Object.assign(estado, { ind: "temp_media", desde: 1981, hasta: 2025, temporada: "anual", zona: "Todas", dep: "", comp: "" }); $("#buscar").value = ""; sincronizar(); dibujar(); };
  $("#buscar").addEventListener("input", () => dibujarTabla(tablaDeptos()));
  $("#descargar").onclick = descargar;
  const tema = $("#tema");
  const ponerTema = (t) => { document.documentElement.dataset.theme = t; tema.textContent = t === "dark" ? "Tema claro" : "Tema oscuro"; try { localStorage.setItem("tema", t); } catch (_) {} };
  let guardado = null; try { guardado = localStorage.getItem("tema"); } catch (_) {}
  ponerTema(guardado || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  tema.onclick = () => { ponerTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark"); franjasCabecera(); dibujar(); };
}
function franjasCabecera() {
  const s = anual(D.nacional, "temp_media", "anual");
  const base = d3.mean(s.filter((d) => d.anio >= BASE[0] && d.anio <= BASE[1]), (d) => d.valor);
  const color = d3.scaleLinear().domain([-1.1, -0.4, 0, 0.4, 1.1]).range(["#104281", "#5598e7", "#e9e7e1", "#ec7f72", "#9c1f1f"]).clamp(true);
  const caja = $("#franjas"); caja.replaceChildren();
  s.forEach((d) => { const c = document.createElement("span"); c.style.background = color(d.valor - base); c.title = `${d.anio}: ${signo(d.valor - base)} °C`; caja.append(c); });
}

/* ---------- Arranque ---------- */
Promise.all([d3.json("data/clima.json"), d3.json("data/peru.geojson")]).then(([datos, geo]) => {
  D = datos; GEO = geo;
  iniciarControles(); sincronizar(); franjasCabecera(); dibujar();
  let t;
  new ResizeObserver(() => { clearTimeout(t); t = setTimeout(dibujar, 120); }).observe($("#rejilla"));
  window.__listo = true;
}).catch((e) => {
  $("#alcance").textContent = "No se pudieron cargar los datos. Recarga la página.";
  console.error(e);
});
