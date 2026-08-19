# Third-party notices

VDR is distributed under the GNU General Public License v3.0 (see [LICENSE](LICENSE)).
It bundles or depends on the third-party components listed below. Each remains under
its own license, reproduced or linked here as those licenses require.

---

## FFmpeg — **GPLv3** (bundled binary)

The distributed macOS app (`VDR.app/Contents/MacOS/ffmpeg`, and therefore the
`VDR Installer.dmg` published on the Releases page) **includes an FFmpeg binary built
with `--enable-gpl --enable-version3`**, which places that binary — and this
application as a whole, since it is distributed together with it — under the
**GNU General Public License, version 3 or later**.

- Project: <https://ffmpeg.org/>
- Version bundled: **9.0.1**
- License: GPLv3 (because of `--enable-gpl`, `--enable-version3`, `--enable-libx264`,
  `--enable-libx265`)
- Build configuration of the bundled binary (from `ffmpeg -version`):

  ```
  --enable-shared --enable-pthreads --enable-version3 --enable-ffplay --enable-gpl
  --enable-libsvtav1 --enable-libopus --enable-libx264 --enable-libmp3lame
  --enable-libdav1d --enable-libvmaf --enable-libvpx --enable-libx265 --enable-openssl
  --enable-videotoolbox --enable-audiotoolbox --enable-neon
  ```

### Written offer for FFmpeg source code

The complete corresponding source code for the bundled FFmpeg build is available from
the FFmpeg project at <https://ffmpeg.org/download.html> and
<https://git.ffmpeg.org/ffmpeg.git> (tag `n9.0.1`). The binary shipped in the DMG is an
unmodified build produced by [Homebrew](https://formulae.brew.sh/formula/ffmpeg); its
build recipe is at
<https://github.com/Homebrew/homebrew-core/blob/main/Formula/f/ffmpeg.rb>.

If you would prefer to receive the corresponding source directly, open an issue on this
repository and it will be provided.

**Note:** VDR only uses FFmpeg to *mux/remux* already-encoded streams (merging separate
video and audio tracks into one MP4) and, optionally, to extract audio to MP3. It does
not re-encode video.

---

## yt-dlp — Unlicense (public domain)

Used for video/stream extraction (`video_capture.py`).

- Project: <https://github.com/yt-dlp/yt-dlp>
- Version: 2026.7.4
- License: The Unlicense — <https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE>

---

## Python packages

| Package | Version | License |
|---|---|---|
| requests | 2.34.2 | Apache-2.0 |
| urllib3 | 2.7.0 | MIT |
| certifi | 2026.7.22 | MPL-2.0 |
| charset-normalizer | 3.5.1 | MIT |
| idna | 3.18 | BSD-3-Clause |
| Flask | 3.1.3 | BSD-3-Clause |
| Werkzeug | 3.1.8 | BSD-3-Clause |
| Jinja2 | 3.1.6 | BSD-3-Clause |
| MarkupSafe | 3.0.3 | BSD-3-Clause |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| click | 8.4.2 | BSD-3-Clause |
| blinker | 1.9.0 | MIT |
| pyobjc-framework-Cocoa | 12.2.2 | MIT |

---

## Build tooling (not redistributed inside the app)

| Tool | License | Note |
|---|---|---|
| PyInstaller | GPLv2-or-later **with a linking exception** | The exception explicitly permits building and distributing non-free programs; the bootloader it embeds does not impose GPL on the bundled application. |
| py2app | MIT | Alternative packaging flow. |
| dmgbuild | MIT | Builds the `.dmg` installer. |

---

## About this project

VDR is an independent, original work. It is not affiliated with, endorsed by, or derived
from the source code of any other download manager. Any resemblance in feature set
reflects the common conventions of the category, not shared code or lineage.
