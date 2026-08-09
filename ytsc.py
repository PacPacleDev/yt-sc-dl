#!/usr/bin/env python3
"""Yt-Sc DL — point d'entrée unique.

    python3 ytsc.py                          ouvre l'interface graphique
    python3 ytsc.py <url>                    télécharge une playlist
    python3 ytsc.py --saved                  synchronise les playlists mémorisées
    python3 ytsc.py <url> -o ~/Music -f aiff options d'encodage
    python3 ytsc.py --help                   aide complète
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ytsc import config                                    # noqa: E402
from ytsc.downloader import download, detect_source, DownloadError  # noqa: E402


def run_gui():
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("✗ tkinter n'est pas disponible — l'interface ne peut pas s'ouvrir.")
        print("  macOS   : brew install python-tk")
        print("  Debian  : sudo apt install python3-tk")
        print("  Windows : réinstalle Python en cochant « tcl/tk »")
        print("\nEn attendant, la ligne de commande fonctionne :")
        print("  python3 ytsc.py <url>")
        return 1
    from ytsc.gui import App
    App().mainloop()
    return 0


def run_cli(args):
    cfg = config.load()

    # Options de ligne de commande prioritaires sur la configuration
    fmt = args.format or cfg["format"]
    quality = args.quality or cfg["quality"]

    targets = []
    if args.saved:
        for key, dirkey in (("youtube_url", "youtube_dir"),
                            ("soundcloud_url", "soundcloud_dir")):
            if cfg.get(key):
                targets.append((cfg[key], args.output or cfg[dirkey]))
        if not targets:
            print("✗ Aucune playlist mémorisée dans config.json.")
            print("  Ajoute-les via l'interface, ou passe une URL directement.")
            return 1
    else:
        out = args.output or cfg["output_dir"]
        targets.append((args.url, out))

    failures = 0
    for url, out in targets:
        if not detect_source(url):
            print(f"✗ URL non reconnue : {url}")
            failures += 1
            continue
        out = os.path.expanduser(out)
        try:
            download(url, out, fmt=fmt, quality=quality,
                     embed_thumbnail=not args.no_thumbnail,
                     embed_metadata=not args.no_metadata,
                     subfolder_per_playlist=not args.flat,
                     on_message=print)
        except DownloadError as e:
            print(f"✗ {e}")
            failures += 1
        print()
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(
        prog="ytsc",
        description="Télécharge des playlists YouTube et SoundCloud en audio, "
                    "prêtes pour Rekordbox. Sans argument, ouvre l'interface.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""exemples :
  python3 ytsc.py                                  interface graphique
  python3 ytsc.py https://youtube.com/playlist?list=…
  python3 ytsc.py <url> -o ~/Music/DJ -f aiff
  python3 ytsc.py --saved                          playlists mémorisées
""")
    p.add_argument("url", nargs="?", help="URL YouTube ou SoundCloud")
    p.add_argument("-o", "--output", help="dossier de destination")
    p.add_argument("-f", "--format", choices=config.FORMATS,
                   help="format audio (défaut : mp3)")
    p.add_argument("-q", "--quality", choices=config.QUALITIES,
                   help="débit en kbps, ignoré si format sans perte")
    p.add_argument("--saved", action="store_true",
                   help="synchronise les playlists enregistrées")
    p.add_argument("--flat", action="store_true",
                   help="ne pas créer de sous-dossier par playlist")
    p.add_argument("--no-thumbnail", action="store_true",
                   help="ne pas intégrer la pochette")
    p.add_argument("--no-metadata", action="store_true",
                   help="ne pas intégrer les métadonnées")
    p.add_argument("--version", action="store_true", help="affiche la version")
    args = p.parse_args()

    if args.version:
        from ytsc import __version__
        print(f"Yt-Sc DL {__version__}")
        return 0

    if not args.url and not args.saved:
        return run_gui()
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
