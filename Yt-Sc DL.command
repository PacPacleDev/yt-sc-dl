#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Yt-Sc DL — double-clique pour ouvrir l'interface (macOS).
#
# Au premier lancement, macOS peut bloquer le fichier :
#   clic droit → Ouvrir → Ouvrir
# ─────────────────────────────────────────────────────────────

cd "$(dirname "$0")" || exit 1

if ! command -v python3 &>/dev/null; then
  echo "✗ Python 3 n'est pas installé."
  echo "  → brew install python-tk"
  read -p "Appuie sur Entrée pour fermer..."
  exit 1
fi

python3 ytsc.py "$@"

if [ $? -ne 0 ]; then
  echo ""
  echo "─────────────────────────────────────────"
  read -p "Appuie sur Entrée pour fermer cette fenêtre..."
fi
