#!/bin/bash
# =============================================================================
# verifier_avant_push.sh — Contrôle qu'aucune donnée personnelle ne part
# sur GitHub. À lancer depuis la racine du dépôt, avant chaque push.
#
#   ./verifier_avant_push.sh
# =============================================================================

cd "$(dirname "$0")" || exit 1
ALERTES=0

echo "╭──────────────────────────────────────────────╮"
echo "│  Vérification avant publication              │"
echo "╰──────────────────────────────────────────────╯"
echo ""

# ── 1. Ce que git s'apprête réellement à envoyer ─────────────────────────────
echo "── Fichiers suivis par git ──"
git ls-files | sed 's/^/   /'
echo ""

# ── 2. Fichiers qui ne devraient JAMAIS être suivis ──────────────────────────
echo "── Fichiers sensibles ──"
SENSIBLES=$(git ls-files | grep -iE '(^|/)(config\.json|\.env|.*\.key|.*\.pem|\.archive_.*\.txt)$|\.(mp3|wav|aiff|flac|m4a|opus|m3u)$')
if [ -n "$SENSIBLES" ]; then
  echo "   ✗ À RETIRER :"
  echo "$SENSIBLES" | sed 's/^/      /'
  ALERTES=$((ALERTES+1))
else
  echo "   ✓ Aucun fichier de config, de clé ni de musique"
fi
echo ""

# ── 3. Contenu des fichiers suivis ───────────────────────────────────────────
echo "── Contenu ──"

# Exemples volontairement présents dans la documentation — pas des fuites
EXEMPLES='user/sets/mix|PLxxxx|<url>|<your-username>|ID\+PSEUDO|exemple\.com|ton-email'

verifier() {
  local libelle="$1" motif="$2"
  local trouve
  trouve=$(git ls-files -z | xargs -0 grep -nIiE "$motif" 2>/dev/null \
           | grep -vE "$EXEMPLES")
  if [ -n "$trouve" ]; then
    echo "   ⚠ $libelle :"
    echo "$trouve" | head -8 | sed 's/^/      /'
    ALERTES=$((ALERTES+1))
  else
    echo "   ✓ $libelle : rien"
  fi
}

verifier "Chemins personnels"  '/Users/[a-z]|/home/[a-z]|C:\\Users\\'
verifier "Adresses e-mail"     '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
verifier "Jetons / mots de passe" '(api[_-]?key|secret|password|passwd|token)[[:space:]]*[=:][[:space:]]*[^[:space:]]{8,}'
verifier "URLs de playlists réelles" '(youtube\.com/playlist\?list=[A-Za-z0-9_-]{16,}|soundcloud\.com/[a-z0-9-]+/sets/[a-z0-9-]+)'
echo ""

# ── 4. Identité utilisée pour les commits ────────────────────────────────────
echo "── Identité git ──"
MAIL=$(git config user.email)
echo "   nom   : $(git config user.name)"
echo "   email : ${MAIL:-<non configuré>}"
if [ -z "$MAIL" ]; then
  echo "   ⚠ Aucune identité git configurée sur cette machine :"
  echo "       git config --global user.name \"TonPseudo\""
  echo "       git config --global user.email \"ID+PSEUDO@users.noreply.github.com\""
  ALERTES=$((ALERTES+1))
elif echo "$MAIL" | grep -q 'users.noreply.github.com'; then
  echo "   ✓ Adresse GitHub anonyme — ton vrai email n'est pas exposé"
else
  echo "   ⚠ Cet email sera visible publiquement dans chaque commit."
  echo "     Pour l'anonymiser : GitHub → Settings → Emails →"
  echo "     « Keep my email address private », puis :"
  echo "       git config --global user.email \"ID+PSEUDO@users.noreply.github.com\""
  ALERTES=$((ALERTES+1))
fi
echo ""

# ── 5. Verdict ───────────────────────────────────────────────────────────────
echo "──────────────────────────────────────────────"
if [ $ALERTES -eq 0 ]; then
  echo "✓ Rien à signaler — tu peux pousser."
else
  echo "⚠ $ALERTES point(s) à vérifier avant de pousser."
fi
echo ""
echo "Rappel : l'historique git est permanent. Supprimer un fichier"
echo "dans un commit suivant ne l'efface pas du dépôt — il reste"
echo "consultable dans les commits précédents."
