# Yt-Sc DL

Download YouTube and SoundCloud playlists as audio files, ready to drop into
Rekordbox. Run it again later and only the new tracks come down.

*[Version française](README.fr.md)*

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

---

## Why

Building a DJ library from online sets means downloading the same playlists
over and over. Yt-Sc DL keeps a record of what it has already fetched, so a
second run pulls only what's new — no duplicates, no re-encoding, no
babysitting.

- **Incremental sync** — an archive file per playlist means nothing is
  downloaded twice
- **DJ-friendly output** — MP3 320, or lossless AIFF / WAV / FLAC
- **Cover art and metadata** embedded, so tracks look right in Rekordbox
- **One folder per playlist**, named after it
- **GUI or command line** — same engine behind both

---

## Install

You need **Python 3.8+** and **ffmpeg**.

```bash
git clone https://github.com/<your-username>/yt-sc-dl.git
cd yt-sc-dl
pip3 install -r requirements.txt
```

Then install ffmpeg, which does the audio conversion:

| Platform | Command |
|---|---|
| macOS | `brew install ffmpeg` |
| Debian / Ubuntu | `sudo apt install ffmpeg` |
| Windows | `winget install ffmpeg` |

For the graphical interface you also need Tk. It ships with Python on most
systems; if the GUI refuses to open, install it:

| Platform | Command |
|---|---|
| macOS | `brew install python-tk` |
| Debian / Ubuntu | `sudo apt install python3-tk` |
| Windows | reinstall Python with the *tcl/tk* option checked |

---

## Use

### Graphical interface

```bash
python3 ytsc.py
```

On macOS you can also double-click **`Yt-Sc DL.command`**. The first time,
macOS will block it — right-click the file, choose **Open**, then **Open**
again. Only needed once.

Paste a playlist URL, pick a destination folder, hit **LANCER**. The two
saved playlists at the top are for the ones you sync regularly: each keeps
its own URL and its own destination.

### Command line

```bash
# One playlist
python3 ytsc.py "https://youtube.com/playlist?list=PLxxxx"

# Choose destination and format
python3 ytsc.py "<url>" -o ~/Music/DJ -f aiff

# Sync both saved playlists
python3 ytsc.py --saved

# Full options
python3 ytsc.py --help
```

| Option | Effect |
|---|---|
| `-o, --output` | Destination folder |
| `-f, --format` | `mp3` `aiff` `wav` `flac` `m4a` `opus` |
| `-q, --quality` | `320` `256` `192` `128` `0` — ignored for lossless formats |
| `--saved` | Sync the playlists stored in `config.json` |
| `--flat` | Don't create a subfolder per playlist |
| `--no-thumbnail` | Skip cover art |
| `--no-metadata` | Skip metadata tags |

---

## How it works

Yt-Sc DL is a thin, opinionated layer over [yt-dlp](https://github.com/yt-dlp/yt-dlp).
Three decisions are worth knowing about.

### Incremental sync

For each playlist, yt-dlp keeps a plain-text file listing the IDs it has
already downloaded:

```
~/Music/
├── .archive_My_Playlist.txt      ← the record
└── My Playlist/
    ├── Track A.mp3
    └── Track B.mp3
```

On the next run, anything listed there is skipped. **Don't delete these
files** — losing one means re-downloading the whole playlist. They sit
next to the playlist folder, not inside it, so they survive if you move
tracks around.

### Bitrate and lossless formats

Bitrate is ignored for AIFF, WAV and FLAC — applying one to a lossless
format is meaningless, so the best available quality is requested instead.
The GUI greys the field out to make this visible.

### Tracking parameters in URLs

Share buttons append parameters that break playlist resolution. SoundCloud's
`?si=…` is stripped entirely; on YouTube only `list=` is kept, since it's the
part that identifies the playlist.

```
https://soundcloud.com/user/sets/mix?si=abc&utm_source=clipboard
                              ↓
https://soundcloud.com/user/sets/mix
```

### Layout

```
yt-sc-dl/
├── ytsc.py              entry point — GUI with no arguments, CLI with them
├── ytsc/
│   ├── config.py        JSON config, sensible defaults
│   ├── downloader.py    the engine: source detection, yt-dlp options, archive
│   └── gui.py           Tk interface
├── Yt-Sc DL.command     macOS double-click launcher
└── requirements.txt
```

`config.json` is created on first save and is gitignored — your playlists and
folders stay yours.

---

## Notes

**Rekordbox and renaming.** Rekordbox stores the exact path of every file.
Rename or move a track after importing it and the link breaks — you lose cue
points and beatgrids. Sort your files *before* importing them.

**Private and region-locked tracks** are skipped with a warning rather than
aborting the whole playlist.

**Only download what you're entitled to.** Respect the terms of service of the
platforms and the rights of the artists.

---

## License

MIT — see [LICENSE](LICENSE).

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [FFmpeg](https://ffmpeg.org/).
