---
name: limpiando-enaho
description: Limpia y une los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, filtra residentes habituales, aplica el factor de expansión y valida la pobreza monetaria contra la cifra oficial (27.6 %). Úsala cuando pidan limpiar, preparar, unir o validar la ENAHO, o calcular pobreza monetaria o extrema del Perú en 2024 por departamento, área urbana o rural, sexo, edad, región o dominio. Las skills graficando-enaho y mapeando-enaho la necesitan antes.
argument-hint: "[--descargar]"
---

# Limpiar la ENAHO 2024

Lo que no se discute (lectura, llaves, filtro, unión, factores, validación) está en `scripts/limpiar.py`.
No lo reescribas ni lo reemplaces con código improvisado: córrelo tal cual.

## Pasos

1. Revisa si existen `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` (966 = ENAHO 2024 en el portal del INEI).
2. Corre exactamente, desde la raíz del proyecto:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py            # si los zip ya están en datos/
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --descargar  # si faltan: los baja del INEI
   ```

3. Lee `salidas/validacion.txt`. Si dice `RESULTADO: FALLÓ` o el script terminó con código 1, **detente**:
   informa qué verificación esencial falló y no calcules nada más. Nunca ajustes cifras para que coincidan.
4. Si aprobó, responde con lo que generó el script:
   - `salidas/indicadores.csv`: pobreza ponderada por nacional, área, sexo, sexo del jefe de hogar, grupo de
     edad, región natural, dominio y departamento, con error estándar, IC 95 % y tamaño de muestra.
   - `salidas/personas_2024.parquet`: la base de 108,664 residentes, para cortes que no estén en la tabla.
5. Para un corte nuevo usa la función ponderada del script, nunca `mean()` simple:

   ```bash
   uv run python -c "
   import sys, pandas as pd; sys.path.insert(0, '${CLAUDE_SKILL_DIR}/scripts')
   from estimacion import proporcion
   b = pd.read_parquet('salidas/personas_2024.parquet')
   print(proporcion(b, 'pobre', dominio=(b.area == 'Rural') & (b.sexo == 'Mujer')))"
   ```

6. Al citar una cifra di: el valor con un decimal, el IC 95 %, «INEI, ENAHO 2024» y el archivo de donde sale.
   Una diferencia entre grupos cuyos IC se superponen no es una diferencia clara: dilo así.
7. Antes de usar una variable que no está en la base, o si piden explicar el método, lee
   [reference.md](reference.md).

## Qué no hacer

- No uses promedios simples: toda proporción va ponderada con `facpob07`.
- No presentes asociaciones como causas.
- No escribas cifras de memoria: si el script o la tabla no la tienen, dilo.
