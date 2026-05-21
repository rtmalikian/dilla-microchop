# Melodic Microchop

**Melodic Microchop** is a sample-based music production tool for creating
melodic microchops from a legally usable audio sample, detecting the pitch of
each tiny chop, and replaying those tuned chops from MIDI. It includes a Python
render engine, a macOS desktop app bundle, a drag-to-Applications DMG builder,
and a native JUCE VST3/AU plugin scaffold for DAW playback.

Author: **Raphael Malikian**  
Email: **rtmalikian@gmail.com**

## Behind The Scenes Walkthrough

Watch the Melodic Microchop video walkthrough and behind-the-scenes creation
process for the Python microchop MIDI sampler.

[Watch the behind-the-scenes creation walkthrough on YouTube](https://youtube.com/live/0w30-Ua9BlY).

## Current Deliverables

- Python CLI render engine for WAV/AIFF + MIDI microchop rendering.
- PySide6 desktop render/export app.
- Local macOS app bundle: `dist/Melodic Microchop.app`.
- Local DMG artifact: `dist/Melodic-Microchop-macOS.dmg`.
- Native JUCE plugin scaffold: `plugin/melodic_microchop_plugin/`.
- Built local VST3: `plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/VST3/Melodic Microchop.vst3`.
- Built local AU: `plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/AU/Melodic Microchop.component`.

Generated app/plugin/release artifacts remain gitignored. Build them locally
from the documented commands.

## What It Does

Melodic Microchop builds a proof-of-concept workflow for:

- melodic microchopping and tiny audio slice generation
- tuned one-shot sample playback from MIDI notes
- automatic pitch detection for chopped audio
- MIDI melody replacement using sample chops instead of a synthesizer
- hip-hop sample chopping, lo-fi beatmaking, and boom-bap melody generation
- offline Python audio rendering with `librosa`, `soundfile`, `numpy`, and `mido`

The render engine takes an existing MIDI file, extracts a target melody track
and bar range, and renders those MIDI notes with short tuned chops from a local
source sample. Render WAV filenames are derived from the selected track name
using a filesystem-safe stem so unusual MIDI track names cannot create nested
output paths.

## Project Status

This is an active local app/plugin prototype. The public repository includes the
source code and build scripts, while generated audio, app bundles, DMGs, and
plugin build outputs remain local:

- Bring your own MIDI file; MIDI generation code is intentionally not included.
- Recording, full production, mastering, and sample-pack pipelines are not
  invoked.
- The Python renderer supports one-shot, gated, looped, stretched, and
  slice-sequence playback modes.
- The JUCE plugin scaffold builds as VST3, AU, and Standalone.
- Plugin chopping/pitch analysis is currently placeholder C++ logic; the Python
  renderer remains the higher-quality analysis path.

## Repository Layout

```text
melodic-microchop/
├── microchop_sampler.py          # main microchop one-shot renderer
├── microchop_desktop_app.py      # local desktop render/export app
├── microchop_requirements.txt    # focused Python dependencies
├── app-daw/                      # app packaging and DAW plugin roadmap
├── plugin/melodic_microchop_plugin/ # native JUCE VST3/AU scaffold
├── original_sample/              # optional local-only sample input folder
├── demo_artifacts/               # public demo render and Ableton analysis file
├── output/                       # generated renders, chops, manifests, reports
└── backups/IMPLEMENTATION_LOG.md # edit and backup log
```

`original_sample/`, `output/`, and `microchop_venv/` are gitignored so large
audio files, generated renders, and local environments are not published.

## Included Demo Artifacts

The repository includes only the public comparison output in
`demo_artifacts/ableton_output/`:

- `main_melody_bars_8_16_microchop.wav` — the final microchop render
- `main_melody_bars_8_16_microchop.wav.asd` — the Ableton analysis file

The copyrighted source sample, generated chops, raw run folders, and reference
audio assets are intentionally excluded from GitHub.

## Setup

Create the required virtual environment:

```bash
python3 -m venv microchop_venv
./microchop_venv/bin/python -m pip install -r microchop_requirements.txt
```

## Local Sample Input

Place any legally usable local audio sample in `original_sample/`, or pass an
absolute path to `--sample`. Pass any compatible MIDI file to `--midi`. Source
recordings, private MIDI generators, and generated chop libraries are
intentionally not included in this repository.

Melodic Microchop does not use the sample BPM for timing. Timing comes from the
provided MIDI file.

## Run The Microchop Render

```bash
./microchop_venv/bin/python microchop_sampler.py \
  --sample original_sample/your_local_sample.wav \
  --midi path/to/your_melody.mid \
  --target-track "Main Melody" \
  --bar-start 8 \
  --bar-count 8 \
  --playback-mode one-shot \
  --style-mode fixed \
  --max-chops 256
```

## Run The Desktop App

```bash
./microchop_venv/bin/python microchop_desktop_app.py
```

The desktop app uses the same render engine as the CLI and provides local file
pickers for the sample, MIDI file, output folder, bar range, playback mode, and
style mode.

Supported playback modes are `one-shot`, `gated`, `loop-forward`,
`loop-forward-reverse`, `loop-reverse-forward`, `stretch`, and
`slice-sequence`.

Supported style modes are `fixed`, `round-robin`, `random-chop`,
`random-playback`, `weighted-random`, `velocity-style`, `note-range-style`,
`alternating-style`, and `humanized-style`.

## Build The macOS App And DMG

```bash
PYINSTALLER_CONFIG_DIR=/private/tmp/microchop-pyinstaller-config \
  ./microchop_venv/bin/pyinstaller --noconfirm --clean app-daw/microchop_desktop.spec

bash app-daw/build_dmg.sh
```

Outputs:

```text
dist/Melodic Microchop.app
dist/Melodic-Microchop-macOS.dmg
```

The DMG script creates a drag-to-Applications disk image and verifies it by
mounting the DMG and checking for the app bundle plus `/Applications` symlink.

## Build The VST3/AU Plugin

```bash
cmake -S plugin/melodic_microchop_plugin \
  -B plugin/melodic_microchop_plugin/build \
  -DCMAKE_BUILD_TYPE=Release

cmake --build plugin/melodic_microchop_plugin/build --config Release
```

Outputs:

```text
plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/VST3/Melodic Microchop.vst3
plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/AU/Melodic Microchop.component
plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/Standalone/Melodic Microchop.app
```

Manual install:

```bash
mkdir -p ~/Library/Audio/Plug-Ins/VST3
mkdir -p ~/Library/Audio/Plug-Ins/Components
cp -R plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/VST3/Melodic\ Microchop.vst3 ~/Library/Audio/Plug-Ins/VST3/
cp -R plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/AU/Melodic\ Microchop.component ~/Library/Audio/Plug-Ins/Components/
```

Validate the AU:

```bash
auval -v aumu Dmcp RMal
```

Each run writes an isolated folder under `output/`:

```text
output/microchop_<timestamp>/
├── midi/input.mid
├── chops/*.wav
├── manifests/chops.json
├── renders/main_melody_bars_8_16_microchop.wav
├── renders/main_melody_bars_8_16_reference.mid
├── renders/main_melody_bars_8_16_reference.wav
├── renders/note_event_map.json
└── reports/
    ├── coverage_report.json
    └── summary.md
```

## How The Sampler Works

1. Load the MIDI file you provide.
2. Parse tempo and time signature from the MIDI.
3. Select `Main Melody` bars 8-16.
4. Detect short audio chop boundaries from the source sample.
5. Estimate each chop's fundamental pitch.
6. Mark uncertain polyphonic piano chops as `unpitched`.
7. Match MIDI notes to exact or nearby pitched chops.
8. Pitch-shift nearby chops to the MIDI note target.
9. Render the verse melody as overlapping one-shot microchops.
10. Export the same 8-bar phrase as reference MIDI and a simple diagnostic tone WAV.
11. Write diagnostics showing chop coverage, pitch-shift distances, and weak
    note coverage.

## Verification

The current local build has been verified with:

- Python compile checks.
- Synthetic render smoke check: `./microchop_venv/bin/python app-daw/smoke_check.py`.
- Desktop app smoke launch.
- Bundled app smoke launch.
- DMG create and mount verification.
- JUCE CMake configure/build.
- VST3/AU bundle existence checks.
- VST3/AU ad-hoc codesign verification.
- AU validation: `auval -v aumu Dmcp RMal`.

## SEO Keywords

melodic microchop sampler, melodic sample chopping, Python audio sampler,
MIDI sample playback, tuned microchops, hip-hop production tool, boom-bap sample
chopper, lo-fi beatmaking Python, microchop MIDI instrument, automatic pitch
detection for samples, one-shot sampler renderer, sample-based music production,
librosa audio chopping, MIDI controlled sample chops, piano sample microchop,
AI-assisted music production tooling.

## License And Sample Rights

No license has been selected yet. Source recordings and generated chops should
only be redistributed when you have the rights to the underlying recording.
