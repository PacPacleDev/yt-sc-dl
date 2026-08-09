"""Yt-Sc DL — télécharge des playlists YouTube et SoundCloud pour Rekordbox."""

__version__ = "1.0.0"

from .downloader import (  # noqa: F401
    download, detect_source, clean_url, DownloadError,
)
