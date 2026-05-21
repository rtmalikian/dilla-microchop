# Melodic Microchop

**Melodic Microchop** is a Python audio and MIDI sampler tool for creating
melodic microchops from a legally usable audio sample, detecting the
pitch of each tiny chop, and replaying those tuned one-shot chops from a MIDI
melody you provide. It is designed for hip-hop producers, sample-based
beatmakers, lo-fi producers, boom-bap producers, and creative coders who want an
offline microchop workflow that turns piano, soul, jazz, vinyl, or field-recorded
audio into a playable MIDI-controlled chop instrument.

Author: **Raphael Malikian**  
Email: **rtmalikian@gmail.com**

## Behind The Scenes Walkthrough

Watch the Melodic Microchop video walkthrough and behind-the-scenes creation
process for the Python microchop MIDI sampler.

[Watch the behind-the-scenes creation walkthrough on YouTube](https://youtube.com/live/0w30-Ua9BlY).

## What It Does

Melodic Microchop builds a proof-of-concept workflow for:

- melodic microchopping and tiny audio slice generation
- tuned one-shot sample playback from MIDI notes
- automatic pitch detection for chopped audio
- MIDI melody replacement using sample chops instead of a synthesizer
- hip-hop sample chopping, lo-fi beatmaking, and boom-bap melody generation
- offline Python audio rendering with `librosa`, `soundfile`, `numpy`, and `mido`

The current POC takes an existing MIDI file, extracts a target melody track and
bar range, and renders those MIDI notes with short one-shot chops from a local
source sample.

## Project Status

This is a local proof of concept. The first version is intentionally focused:

- Bring your own MIDI file; MIDI generation code is intentionally not included.
- Recording, full production, mastering, and sample-pack pipelines are not
  invoked.
- Playback mode is `one-shot`: MIDI note-off messages do not cut the chop.
- Short chops are preferred over long sustained sample regions.
- Pitch shifting is expected when exact note coverage is missing.

Future playback modes to implement:

- `gated`: stop playback at MIDI note-off
- `stretch`: time-stretch chops to MIDI note duration
- `loop`: loop a stable tonal region until note-off
- `slice-sequence`: step through chops in order regardless of pitch

## Repository Layout

```text
melodic-microchop/
├── microchop_sampler.py          # main microchop one-shot renderer
├── microchop_desktop_app.py      # local desktop render/export app
├── microchop_requirements.txt    # focused Python dependencies
├── app-daw/                      # app packaging and DAW plugin roadmap
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
