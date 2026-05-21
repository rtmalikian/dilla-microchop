# Dilla Microchop App And DAW Packaging

This folder tracks the application and DAW-plugin direction for Dilla Microchop.
The first implemented app target is a local desktop render/export wrapper around
the shared Python renderer.

## Desktop App V1

Run the desktop app from the project root:

```bash
./microchop_venv/bin/python microchop_desktop_app.py
```

The app lets users choose a local audio sample, a local MIDI file, target track,
bar range, chop settings, playback mode, and variation style. Rendering happens
through the same `render_job()` path used by the CLI.

## CLI

The CLI remains available:

```bash
./microchop_venv/bin/python microchop_sampler.py \
  --sample /path/to/sample.wav \
  --midi /path/to/melody.mid \
  --target-track "Main Melody" \
  --bar-start 8 \
  --bar-count 8 \
  --playback-mode one-shot \
  --style-mode fixed
```

## Playback Modes

- `one-shot`: play the full chop from MIDI note-on.
- `gated`: stop at MIDI note-off with a release fade.
- `loop-forward`: loop forward until MIDI note-off.
- `loop-forward-reverse`: ping-pong forward then reverse.
- `loop-reverse-forward`: ping-pong reverse then forward.
- `stretch`: resample the chop to the MIDI note duration.
- `slice-sequence`: reserved for sequence-based triggering.

## Style Modes

- `fixed`: use the chosen playback mode for every event.
- `round-robin`: rotate repeated notes through compatible chops.
- `random-chop`: randomly choose compatible chops.
- `random-playback`: randomly choose from enabled playback modes.
- `weighted-random`: choose playback modes from weighted settings.
- `velocity-style`: choose playback behavior from MIDI velocity.
- `note-range-style`: choose playback behavior from MIDI note range.
- `alternating-style`: cycle through a configured playback mode list.
- `humanized-style`: vary chop choice, start offset, gain, pan, pitch cents, and
  playback mode within limits.

## macOS Packaging

Install dependencies in the existing virtual environment:

```bash
./microchop_venv/bin/python -m pip install -r microchop_requirements.txt
```

Build the app bundle:

```bash
PYINSTALLER_CONFIG_DIR=/private/tmp/microchop-pyinstaller-config \
  ./microchop_venv/bin/pyinstaller --noconfirm --clean app-daw/microchop_desktop.spec
```

The app bundle will be written under `dist/Dilla Microchop.app`. Build outputs
must remain local and should not be committed.

## Future DAW Plugin

The plugin should be a later JUCE or iPlug2 product that loads prepared chop
kits exported by the desktop app. The plugin should not run onset detection,
librosa pitch analysis, or batch rendering in the DAW audio thread.

## Rights Boundary

Do not commit or package copyrighted source samples, generated chop folders,
private MIDI generation scripts, private MIDI files, or local render output.

## Smoke Checks

Run a self-contained verification that creates synthetic audio and MIDI in a
temporary folder:

```bash
./microchop_venv/bin/python app-daw/smoke_check.py
```
