# Yt-Sc DL

Télécharge des playlists YouTube et SoundCloud en fichiers audio, prêtes à
glisser dans Rekordbox. Relance-le plus tard : seuls les nouveaux morceaux
descendent.

*[English version](README.md)*

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

---

## Pourquoi

Se constituer une bibliothèque DJ à partir de sets en ligne, c'est
retélécharger les mêmes playlists encore et encore. Yt-Sc DL retient ce qu'il
a déjà récupéré : la deuxième passe ne prend que les nouveautés. Pas de
doublons, pas de réencodage, rien à surveiller.

- **Synchronisation incrémentale** — un fichier d'archive par playlist, rien
  n'est téléchargé deux fois
- **Sortie pensée pour le mix** — MP3 320, ou AIFF / WAV / FLAC sans perte
- **Pochette et métadonnées intégrées**, pour que les morceaux s'affichent
  correctement dans Rekordbox
- **Un dossier par playlist**, nommé d'après elle
- **Interface ou ligne de commande** — le même moteur derrière les deux

---

## Installation

Il te faut **Python 3.8+** et **ffmpeg**.

```bash
git clone https://github.com/<ton-pseudo>/yt-sc-dl.git
cd yt-sc-dl
pip3 install -r requirements.txt
```

Puis ffmpeg, qui fait la conversion audio :

| Plateforme | Commande |
|---|---|
| macOS | `brew install ffmpeg` |
| Debian / Ubuntu | `sudo apt install ffmpeg` |
| Windows | `winget install ffmpeg` |

Pour l'interface graphique, il faut aussi Tk. Il est livré avec Python sur la
plupart des systèmes ; si la fenêtre refuse de s'ouvrir :

| Plateforme | Commande |
|---|---|
| macOS | `brew install python-tk` |
| Debian / Ubuntu | `sudo apt install python3-tk` |
| Windows | réinstaller Python en cochant *tcl/tk* |

---

## Utilisation

### Interface graphique

```bash
python3 ytsc.py
```

Sur macOS, tu peux aussi double-cliquer sur **`Yt-Sc DL.command`**. La
première fois, macOS le bloquera : clic droit sur le fichier → **Ouvrir** →
**Ouvrir**. Une seule fois.

Colle une URL de playlist, choisis un dossier, clique sur **LANCER**. Les deux
playlists mémorisées en haut servent à celles que tu synchronises
régulièrement : chacune garde son URL et son dossier de destination.

### Ligne de commande

```bash
# Une playlist
python3 ytsc.py "https://youtube.com/playlist?list=PLxxxx"

# Choisir la destination et le format
python3 ytsc.py "<url>" -o ~/Music/DJ -f aiff

# Synchroniser les deux playlists mémorisées
python3 ytsc.py --saved

# Toutes les options
python3 ytsc.py --help
```

| Option | Effet |
|---|---|
| `-o, --output` | Dossier de destination |
| `-f, --format` | `mp3` `aiff` `wav` `flac` `m4a` `opus` |
| `-q, --quality` | `320` `256` `192` `128` `0` — ignoré si format sans perte |
| `--saved` | Synchronise les playlists de `config.json` |
| `--flat` | Ne pas créer de sous-dossier par playlist |
| `--no-thumbnail` | Sans pochette |
| `--no-metadata` | Sans métadonnées |

---

## Fonctionnement

Yt-Sc DL est une fine couche au-dessus de
[yt-dlp](https://github.com/yt-dlp/yt-dlp). Trois choix méritent une
explication.

### Synchronisation incrémentale

Pour chaque playlist, yt-dlp tient un fichier texte listant les identifiants
déjà téléchargés :

```
~/Music/
├── .archive_Ma_Playlist.txt      ← la mémoire
└── Ma Playlist/
    ├── Morceau A.mp3
    └── Morceau B.mp3
```

À la relance, tout ce qui y figure est ignoré. **Ne supprime pas ces
fichiers** : en perdre un, c'est retélécharger la playlist entière. Ils sont
posés à côté du dossier, pas dedans, pour survivre si tu réorganises tes
morceaux.

### Débit et formats sans perte

Le débit est ignoré pour AIFF, WAV et FLAC — lui appliquer une valeur n'aurait
aucun sens, on demande donc la meilleure qualité disponible. L'interface grise
le champ pour que ce soit visible.

### Paramètres de suivi dans les URL

Les boutons « partager » ajoutent des paramètres qui cassent la résolution de
playlist. Le `?si=…` de SoundCloud est retiré entièrement ; sur YouTube seul
`list=` est conservé, puisque c'est lui qui identifie la playlist.

```
https://soundcloud.com/user/sets/mix?si=abc&utm_source=clipboard
                              ↓
https://soundcloud.com/user/sets/mix
```

### Organisation du code

```
yt-sc-dl/
├── ytsc.py              point d'entrée — interface sans argument, CLI avec
├── ytsc/
│   ├── config.py        configuration JSON et valeurs par défaut
│   ├── downloader.py    le moteur : détection, options yt-dlp, archive
│   └── gui.py           interface Tk
├── Yt-Sc DL.command     lanceur macOS
└── requirements.txt
```

`config.json` est créé au premier enregistrement et n'est pas versionné : tes
playlists et tes dossiers restent chez toi.

---

## Bon à savoir

**Rekordbox et le renommage.** Rekordbox mémorise le chemin exact de chaque
fichier. Renommer ou déplacer un morceau après l'avoir importé casse le lien —
tu perds cue points et beatgrids. Range tes fichiers *avant* de les importer.

**Les morceaux privés ou bloqués géographiquement** sont ignorés avec un
avertissement, sans interrompre le reste de la playlist.

**Ne télécharge que ce à quoi tu as droit.** Respecte les conditions
d'utilisation des plateformes et les droits des artistes.

---

## Licence

MIT — voir [LICENSE](LICENSE).

Repose sur [yt-dlp](https://github.com/yt-dlp/yt-dlp) et
[FFmpeg](https://ffmpeg.org/).
