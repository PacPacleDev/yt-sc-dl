"""Téléchargement de playlists YouTube et SoundCloud vers des fichiers audio.

Le module s'appuie sur yt-dlp. Deux points méritent une explication :

**L'archive.** yt-dlp tient un fichier texte listant les identifiants déjà
téléchargés. C'est ce qui permet de relancer une synchronisation et de ne
récupérer que les nouveautés. Le fichier est nommé d'après la playlist et
posé à côté d'elle — le déplacer ou le supprimer provoque un
retéléchargement complet.

**Le débit.** L'option est ignorée pour les formats sans perte (AIFF, WAV,
FLAC) : y appliquer un débit n'aurait pas de sens, on demande alors la
meilleure qualité disponible.
"""

import os
import re
import unicodedata

SOURCE_YOUTUBE = "youtube"
SOURCE_SOUNDCLOUD = "soundcloud"

LOSSLESS = {"aiff", "wav", "flac"}


class DownloadError(RuntimeError):
    """Erreur bloquante : dépendance absente, URL invalide, dossier illisible."""


# ── Détection de la source ───────────────────────────────────────────────────
def detect_source(url):
    """Retourne 'youtube', 'soundcloud' ou None."""
    u = (url or "").strip().lower()
    if "youtube.com" in u or "youtu.be" in u:
        return SOURCE_YOUTUBE
    if "soundcloud.com" in u:
        return SOURCE_SOUNDCLOUD
    return None


def clean_url(url):
    """Retire les paramètres de suivi ajoutés par les boutons « partager ».

    Sur SoundCloud le « ?si=… » casse la résolution de playlist, on tronque.
    Sur YouTube le « list= » est indispensable, on ne garde que lui.
    """
    url = (url or "").strip()
    if not url:
        return url
    if detect_source(url) == SOURCE_SOUNDCLOUD:
        return url.split("?")[0]
    if detect_source(url) == SOURCE_YOUTUBE and "list=" in url:
        base, _, query = url.partition("?")
        keep = [p for p in query.split("&") if p.startswith("list=")]
        if keep:
            return f"{base}?{'&'.join(keep)}"
    return url


# ── Nommage ──────────────────────────────────────────────────────────────────
def safe_name(name, fallback="Playlist"):
    """Nom de dossier utilisable sur macOS, Linux et Windows."""
    name = (name or "").strip()
    if not name:
        return fallback
    name = "".join(c for c in unicodedata.normalize("NFKC", name)
                   if unicodedata.category(c)[0] != "C")
    name = re.sub(r'[/\\:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:120] or fallback


def archive_path(base_dir, playlist_name):
    slug = re.sub(r"\W+", "_", safe_name(playlist_name)).strip("_") or "playlist"
    return os.path.join(base_dir, f".archive_{slug}.txt")


# ── yt-dlp ───────────────────────────────────────────────────────────────────
def _import_ytdlp():
    try:
        import yt_dlp
    except ImportError as e:
        raise DownloadError(
            "yt-dlp n'est pas installé.\n"
            "  pip3 install -r requirements.txt\n"
            "  (ou : pip3 install yt-dlp)") from e
    return yt_dlp


class _SilentLogger:
    """Absorbe la sortie de yt-dlp.

    `quiet=True` ne suffit pas : yt-dlp écrit ses erreurs directement sur
    stderr tant qu'aucun logger n'est fourni.
    """

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def fetch_playlist_title(url):
    """Titre de la playlist, sans rien télécharger. None si indisponible."""
    yt_dlp = _import_ytdlp()
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True,
            "skip_download": True, "logger": _SilentLogger()}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        return None
    if not info:
        return None
    return info.get("playlist_title") or info.get("title")


def build_options(output_dir, fmt="mp3", quality="320", embed_thumbnail=True,
                  embed_metadata=True, archive=None, progress_hook=None,
                  logger=None):
    """Construit le dictionnaire d'options yt-dlp."""
    postprocessors = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": fmt,
        # yt-dlp attend une chaîne ; « 0 » signifie « meilleure qualité »
        "preferredquality": "0" if fmt in LOSSLESS else str(quality),
    }]
    if embed_metadata:
        postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if embed_thumbnail:
        # Doit venir après l'extraction audio pour que le conteneur existe
        postprocessors.append({"key": "EmbedThumbnail",
                               "already_have_thumbnail": False})

    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "postprocessors": postprocessors,
        "writethumbnail": embed_thumbnail,
        "ignoreerrors": True,       # une vidéo privée ne doit pas tout stopper
        "no_warnings": True,
        "quiet": True,
        "noprogress": True,
        "consoletitle": False,
    }
    if archive:
        opts["download_archive"] = archive
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    if logger:
        opts["logger"] = logger
    return opts


# ── Point d'entrée ───────────────────────────────────────────────────────────
def download(url, base_dir, fmt="mp3", quality="320", embed_thumbnail=True,
             embed_metadata=True, subfolder_per_playlist=True,
             on_message=None, on_progress=None):
    """Télécharge une playlist ou une piste.

    `on_message(str)` reçoit les messages destinés à l'utilisateur,
    `on_progress(dict)` les événements bruts de yt-dlp.

    Retourne un dictionnaire : {'dir', 'playlist', 'downloaded', 'skipped'}.
    """
    say = on_message or (lambda _m: None)

    url = clean_url(url)
    source = detect_source(url)
    if not source:
        raise DownloadError("URL non reconnue — attendu YouTube ou SoundCloud.")

    if not base_dir or not os.path.isdir(base_dir):
        raise DownloadError(f"Dossier de destination introuvable : {base_dir}")

    yt_dlp = _import_ytdlp()

    say(f"▶ Source : {source}")
    say(f"  URL    : {url}")

    title = fetch_playlist_title(url) or (
        "YouTube Playlist" if source == SOURCE_YOUTUBE else "SoundCloud Playlist")
    playlist = safe_name(title)

    output_dir = os.path.join(base_dir, playlist) if subfolder_per_playlist else base_dir
    os.makedirs(output_dir, exist_ok=True)

    say(f"  Dossier : {output_dir}")
    say(f"  Format  : {fmt}"
        + ("" if fmt in LOSSLESS else f" / {quality} kbps"))

    stats = {"downloaded": 0, "skipped": 0, "errors": 0}

    def hook(d):
        if d.get("status") == "finished":
            stats["downloaded"] += 1
            name = os.path.basename(d.get("filename", ""))
            say(f"  ✓ {os.path.splitext(name)[0][:70]}")
        if on_progress:
            on_progress(d)

    class _Logger:
        def debug(self, msg):
            # yt-dlp signale ici les morceaux déjà présents dans l'archive
            if "has already been recorded" in msg or "already been downloaded" in msg:
                stats["skipped"] += 1

        def info(self, msg):
            pass

        def warning(self, msg):
            pass

        def error(self, msg):
            stats["errors"] += 1
            # Une seule ligne suffit : le détail technique noie l'utilisateur
            first = str(msg).split("; please report")[0].strip()
            say(f"  ✗ {first[:200]}")

    opts = build_options(
        output_dir, fmt=fmt, quality=quality,
        embed_thumbnail=embed_thumbnail, embed_metadata=embed_metadata,
        archive=archive_path(base_dir, playlist),
        progress_hook=hook, logger=_Logger())

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise DownloadError(f"Échec du téléchargement : {e}") from e

    if stats["downloaded"]:
        msg = f"✓ {stats['downloaded']} nouveaux morceaux dans {output_dir}"
        if stats["errors"]:
            msg += f"  ({stats['errors']} en échec)"
        say(msg)
    elif stats["errors"]:
        # `ignoreerrors` empêche l'exception : sans ce garde-fou, un échec
        # total serait annoncé comme « rien de neuf ».
        raise DownloadError(
            "Aucune piste récupérée. Vérifie l'URL, ta connexion, "
            "et que la playlist est publique.")
    else:
        say("✓ Aucune nouveauté — tout est déjà à jour.")

    return {"dir": output_dir, "playlist": playlist, **stats}
