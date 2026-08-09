"""Chargement et sauvegarde de la configuration.

La configuration vit dans un simple JSON à côté du programme. Elle n'est
jamais versionnée (voir .gitignore) : chacun a ses playlists et ses dossiers.
"""

import os
import json
import copy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

FORMATS = ["mp3", "aiff", "wav", "flac", "m4a", "opus"]
LOSSLESS = {"aiff", "wav", "flac"}
QUALITIES = ["320", "256", "192", "128", "0"]

DEFAULTS = {
    # Deux sources mémorisées, chacune avec son dossier de destination
    "youtube_url": "",
    "youtube_dir": "",
    "soundcloud_url": "",
    "soundcloud_dir": "",
    # Dossier utilisé pour les téléchargements ponctuels
    "output_dir": "",
    # Options d'encodage
    "format": "mp3",
    "quality": "320",
    "embed_thumbnail": True,
    "embed_metadata": True,
    # Un sous-dossier par playlist, nommé d'après elle
    "subfolder_per_playlist": True,
}


def load(path=CONFIG_PATH):
    """Retourne la configuration, complétée par les valeurs par défaut."""
    cfg = copy.deepcopy(DEFAULTS)
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (OSError, ValueError):
            pass  # config illisible : on repart des valeurs par défaut

    # Le dossier par défaut ne peut pas être décidé à l'avance : on prend
    # « Musique » de l'utilisateur, ou le dossier courant à défaut.
    if not cfg["output_dir"]:
        cfg["output_dir"] = default_music_dir()
    for key in ("youtube_dir", "soundcloud_dir"):
        if not cfg[key]:
            cfg[key] = cfg["output_dir"]
    return cfg


def save(cfg, path=CONFIG_PATH):
    """Écrit la configuration. Renvoie None si tout va bien, l'erreur sinon."""
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        return None
    except OSError as e:
        return e


def default_music_dir():
    """Dossier musique de l'utilisateur, selon la plateforme."""
    for candidate in (os.path.join(os.path.expanduser("~"), "Music"),
                      os.path.join(os.path.expanduser("~"), "Musique"),
                      os.path.join(os.path.expanduser("~"), "Musik")):
        if os.path.isdir(candidate):
            return candidate
    return os.getcwd()
