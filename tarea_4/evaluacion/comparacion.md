# Comparación: Claude Code sin y con MCP/Skills

## Diseño del experimento

- **10 preguntas** ([`preguntas.csv`](preguntas.csv)): 4 del BCRP, 4 de la ENAHO 2024 y 2 que combinan ambas fuentes.
  Incluyen datos puntuales (inflación 2022, tipo de cambio), un cálculo (el máximo de 60 meses), una cifra revisada
  (PBI 2024), tasas por área y por departamento, y dos preguntas mixtas que además exigen interpretar.
- **Respuestas esperadas** fijadas antes de correr el experimento a partir de las fuentes oficiales: API del BCRP,
  cifras publicadas por el INEI y referencias de la Sesión 16. Se confirmaron con cálculos independientes del agente
  ([`verificar_esperadas.py`](verificar_esperadas.py) → [`verificacion_esperadas.csv`](verificacion_esperadas.csv),
  10/10). No se cambiaron después de ver los resultados.
- **Tolerancias definidas de antemano:** ±0.05 pp en series del BCRP, ±0.005 S/ en el tipo de cambio; ±0.1 pp en la
  pobreza nacional (la consigna); ±0.2 pp en tasas subnacionales (redondeo y diferencia documentada entre los dos
  métodos de ponderación); ±0.3 pp en la brecha, que suma dos tasas. El mes, el departamento y el sí/no deben coincidir.
- **Preguntas mixtas:** son correctas solo si las cifras están dentro de tolerancia **y** se cumple el criterio de
  interpretación (no afirmar causalidad; si se relacionan las variables, advertir que vienen de fuentes y niveles
  distintos). Esa revisión se hizo leyendo cada respuesta y quedó anotada con su justificación en
  [`revision_interpretacion.csv`](revision_interpretacion.csv).
- **Calificación de las cifras:** automática, a partir de la línea final `RESPUESTA:` que piden las instrucciones
  ([`evaluar.py`](evaluar.py), función `comparar`).

## Condiciones

| | Modo A · sin MCP ni Skills | Modo B · con MCP y Skills |
|---|---|---|
| Modelo | `claude-opus-5-5` (Claude Code 2.1.319) | el mismo |
| Instrucciones | las mismas (`--append-system-prompt`, ver [`configuracion_experimento.json`](configuracion_experimento.json)) | las mismas |
| Sesiones | una sesión nueva de `claude -p` por pregunta | igual |
| Carpeta | carpeta vacía fuera del repositorio | `tarea_4/` |
| MCP | ninguno (`--strict-mcp-config` sin servidores) | solo `bcrp` (`--mcp-config .mcp.json --strict-mcp-config`) |
| Skills | desactivadas (`--disallowedTools Skill`) | las 3 del proyecto |
| Otras herramientas | Read, Glob, Grep, WebSearch, WebFetch y Bash limitado (`uv run`, `python3`, `ls`, `cat`, `head`, `wc`, `echo`, `test`) | las mismas, más Write y Edit |

Para que el modo A no viera respuestas ya calculadas: corrió fuera del repositorio y **antes** de publicarlo en GitHub,
así que tampoco podía encontrar nuestros resultados en la web. Se revisaron sus 10 sesiones y ninguna leyó archivos del
proyecto: solo hizo búsquedas web, abrió páginas públicas y consultó la API pública del BCRP.

## Resultados

| Métrica | Modo A (sin) | Modo B (con) |
|---|---|---|
| **Respuestas correctas** | **9/10** | **10/10** |
| Incorrectas | 1 (B2) | 0 |
| Sin respuesta o con error | 0 | 0 |
| Respondidas solo de memoria, sin consultar ninguna fuente | 4 (B1, B4, E1, M1) | 0 |
| Tiempo promedio por pregunta | 35.1 s | 21.0 s |
| Tiempo mediano | 36.2 s | 18.5 s |
| Costo total estimado (10 preguntas) | US$ 1.20 | US$ 1.67 |
| Correctas por tipo: BCRP / ENAHO / mixtas | 3/4 · 4/4 · 2/2 | 4/4 · 4/4 · 2/2 |

| Pregunta | A | B | Tiempo A | Tiempo B | Herramientas en B |
|---|---|---|---|---|---|
| B1 Inflación 2022 | ✅ 8.46 (de memoria) | ✅ 8.46 | 7 s | 20 s | `buscar_series`, `serie`, `resumen` |
| B2 PBI 2024 | ❌ 3.3 | ✅ 3.52 | 69 s | 17 s | `buscar_series`, `serie` |
| B3 Tipo de cambio dic. 2024 | ✅ 3.737 (API vía web) | ✅ 3.7366 | 27 s | 13 s | `buscar_series`, `serie` |
| B4 Máximo de la inflación 2020-2024 | ✅ jun. 2022, 8.81 (de memoria) | ✅ jun. 2022, 8.81 | 9 s | 16 s | `buscar_series`, `resumen`, `serie` |
| E1 Pobreza nacional | ✅ 27.6 (de memoria) | ✅ 27.6 | 8 s | 12 s | lee `salidas/validacion.txt` |
| E2 Pobreza rural | ✅ 39.3 (web) | ✅ 39.3 | 46 s | 15 s | lee `salidas/indicadores.csv` |
| E3 Pobreza en Cusco | ✅ 18.5 (web) | ✅ 18.5 | 62 s | 24 s | skill `limpiando-enaho` |
| E4 Departamento más pobre | ✅ Cajamarca, 45.0 (web) | ✅ Cajamarca, 45.0 | 53 s | 35 s | skill `limpiando-enaho` |
| M1 Inflación 2024 + pobreza + ¿causa? | ✅ 1.97; 27.6; no (de memoria) | ✅ 1.97; 27.6; no | 20 s | 30 s | `serie` + `validacion.txt` |
| M2 Caída de la inflación + brecha | ✅ 6.49; 14.5 (web) | ✅ 6.49; 14.5 | 49 s | 29 s | `buscar_series`, `resumen` + `indicadores.csv` |

Detalle por pregunta, con fuentes, herramientas, turnos, costo y enlace a cada sesión: [`resultados.csv`](resultados.csv).
Sesiones completas: [`../evidencias_ia/evaluacion/`](../evidencias_ia/evaluacion/).

### Preguntas que mejoraron o empeoraron

- **Mejoró: B2 (PBI 2024).** El modo A tardó 69 s en buscar en la web y respondió **3.3 %**, la cifra preliminar que
  el BCRP publicó en febrero de 2025. La serie oficial vigente (PM04923AA) dice **3.52 %**, porque las cuentas
  nacionales se revisaron. El modo B consultó la serie y obtuvo el valor actual en 17 s. Es el error típico de
  responder con lo que «se sabe» o con lo que repite la prensa: datos que fueron correctos y ya no lo son.
- **Empeoró: ninguna.**
- **Más rápidas en B:** las preguntas que en A exigieron buscar en la web (B2, B3, E2, E3, E4, M2), con un ahorro
  de 29 s en promedio (51 s frente a 22 s). Donde A respondió de memoria (B1, B4, E1, M1), A fue más rápido: no consultó nada.

### Principales errores y observaciones

1. **Dato desactualizado (A, B2):** la web devuelve primero la cifra preliminar más citada, no la revisada.
2. **Respuestas sin respaldo (A):** 4 de las 9 correctas del modo A salieron de memoria, sin consultar ninguna fuente
   en la sesión. Eran correctas, pero nada en la sesión permitía comprobarlas. En M1 el modelo lo reconoció («salen de
   lo que ya sé y no las comprobé en línea»). En el modo B, las 10 respuestas citan el código de serie y la URL de la
   API, o el archivo de `salidas/` de donde salió la cifra.
3. **Fuentes secundarias (A):** para la ENAHO, el modo A no pudo abrir las páginas del INEI (bloquearon el acceso
   automático) y se apoyó en notas de prensa (Forbes, Infobae, IPE). Acertó porque esas notas reproducían bien la cifra
   oficial.
4. **Uso de salidas ya calculadas (B):** en E1, E2, M1 y M2 el modo B leyó `salidas/validacion.txt` o
   `salidas/indicadores.csv` en vez de volver a correr la skill. Son productos de las skills y validados, así que es
   un atajo legítimo, pero la skill solo se activó cuando la cifra no estaba en un archivo a la vista (E3, E4).
5. **Interpretación:** en las preguntas mixtas, los dos modos rechazaron la conclusión causal con buenas razones. El
   modo B, además, mostró la brecha rural-urbana con los dos métodos de ponderación y eligió el oficial con una
   justificación.

### Prueba de robustez (opcional)

Dos pedidos sin respuesta válida ([`preguntas_robustez.csv`](preguntas_robustez.csv) →
[`resultados_robustez.csv`](resultados_robustez.csv)): la inflación de 2030 y la pobreza del distrito de Miraflores
(la ENAHO no es representativa a nivel distrital). Los dos modos respondieron **NO DISPONIBLE** en los 2 casos (4/4).
En B, el agente buscó la serie y confirmó con el MCP que no había datos para 2030 antes de responder.

## Conclusión

- **Exactitud:** MCP y Skills subieron los aciertos de 9 a 10. La mejora es pequeña porque el modelo base, con búsqueda
  web, ya conoce bien las cifras muy difundidas, como la pobreza nacional o la inflación anual. La diferencia aparece
  justo donde el conocimiento general falla: un **dato revisado** (PBI 2024).
- **Trazabilidad:** con las herramientas, el 100 % de las respuestas cita una fuente oficial consultada en la sesión
  (código de serie y URL, o archivo generado por un script validado). Sin ellas, el 40 % de las respuestas no tenía
  ningún respaldo en la sesión. Para un trabajo de investigación, esto pesa más que el punto de exactitud.
- **Tiempo y costo:** el modo B fue un 40 % más rápido en promedio (21 s frente a 35 s), porque una llamada al MCP
  reemplaza varias búsquedas web. Costó algo más (US$ 1.67 frente a 1.20), sobre todo porque las descripciones de las
  herramientas y las skills ocupan contexto.
- **Lo que este experimento no mide bien:** 10 preguntas sobre cifras publicadas favorecen al modelo sin herramientas.
  Cuando se piden cortes que nadie publicó (pobreza por sexo del jefe de hogar, intervalos de confianza o una
  comparación entre dos periodos de una serie), el modo A tendría que calcularlos desde los microdatos o la API sin
  ayuda, y es ahí donde las Skills y el MCP marcan la mayor diferencia. Además, cada pregunta se corrió una sola vez,
  así que no se mide la variabilidad entre ejecuciones.

**En suma:** MCP y Skills no hacen al modelo «más inteligente». Lo vuelven **verificable, actualizado y más rápido**:
cada cifra sale de una llamada que cualquiera puede repetir.
