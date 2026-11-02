#!/usr/bin/env bash
# Último paso del reel: clona tu voz, regenera subtítulos y video, y lo abre para que lo revises.
#   bash reel/finalizar_reel.sh --aprobar      (primero: pasa el PR de la rama tarea-3 a main)
#   bash reel/finalizar_reel.sh ~/Desktop/mi_voz.m4a
#   bash reel/finalizar_reel.sh --publicar     (después de revisarlo: lo sube a GitHub)
#   bash reel/finalizar_reel.sh --linkedin URL (agrega el enlace de tu publicación al README y a la entrega)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "${1:-}" = "--aprobar" ]; then
  gh pr merge tarea-3 --merge --delete-branch
  git checkout -q main
  git pull -q origin main
  echo "Listo: tarea_3 ya está en main."
  exit 0
fi

if [ "${1:-}" = "--linkedin" ]; then
  [ $# -eq 2 ] || { echo "Uso: bash reel/finalizar_reel.sh --linkedin URL"; exit 1; }
  sed -i '' "s|PENDIENTE_LINKEDIN|$2|g" README.md entrega_issue.md
  git add README.md entrega_issue.md
  git commit -q -m "docs: enlace a la publicación de LinkedIn"
  git push -q origin main
  echo "Listo: enlace de LinkedIn agregado. El texto para el Issue está en entrega_issue.md"
  exit 0
fi

if [ "${1:-}" = "--publicar" ]; then
  [ -f reel/reel.mp4 ] || { echo "Aún no existe reel/reel.mp4"; exit 1; }
  git rm -q --cached --ignore-unmatch reel/reel_borrador.mp4
  rm -f reel/reel_borrador.mp4
  git add reel/reel.mp4 reel/subtitulos.srt reel/tiempos.json
  sed -i '' 's/^> \*\*Estado del reel:.*$/> **Estado del reel:** versión final con voz clonada a partir de la voz de la autora./' README.md
  git add README.md
  git commit -q -m "reel: versión final con voz clonada de la autora"
  git push -q origin main
  echo "Listo: reel subido a GitHub."
  exit 0
fi

[ $# -ge 1 ] || { echo "Uso: bash reel/finalizar_reel.sh RUTA_A_TU_AUDIO"; exit 1; }
[ -f "$1" ] || { echo "No encuentro el audio: $1"; exit 1; }

caffeinate -is .venv-voz/bin/python reel/narrar.py --voz "$1"
caffeinate -is .venv/bin/python reel/construir_reel.py
.venv/bin/python reel/verificar_guion.py
echo
echo "Reel creado en $(pwd)/reel/reel.mp4. Revisa que se entienda y que las cifras suenen bien."
open reel/reel.mp4 || true
echo "Si está bien, ejecuta: bash reel/finalizar_reel.sh --publicar"
