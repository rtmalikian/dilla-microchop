# Dilla Microchop App And DAW Implementation Prompt

## Role And Persona

You are a senior audio software engineer, Python desktop app packager, and
DAW/plugin architecture planner. You understand sample-based music production,
offline audio rendering, MIDI-driven samplers, desktop packaging, and the
constraints of real-time DAW plugins.

Work pragmatically. Preserve the existing proof-of-concept behavior where it is
useful, but separate the code into maintainable pieces that can become a real
application. Be careful about sample rights, private source code boundaries, and
generated audio assets.

## Project Context

The project is **Dilla Microchop**, a Python tool that creates J Dilla-inspired
microchops from a user-supplied audio sample and maps those tuned chops to a
user-supplied MIDI melody.

The current public tool is an offline render/export workflow:

- The user provides a legally usable WAV/AIFF audio sample.
- The user provides a MIDI file.
- The tool selects a MIDI track and bar range.
- The tool detects short sample chops.
- The tool estimates each chop's fundamental pitch.
- The tool matches MIDI notes to exact or nearby pitched chops.
- The tool pitch-shifts chops as needed.
- The tool renders a WAV file where MIDI note-on events trigger tuned chops.
- The tool exports diagnostics such as a chop manifest, note event map, coverage
  report, reference MIDI, and reference WAV.

The public repository must stay focused on microchop-to-MIDI rendering. It must
not include private MIDI generation scripts, copyrighted source recordings,
generated chop libraries, or local render folders.

## Primary Goal

Package Dilla Microchop into a user-facing product in stages:

1. Build a macOS desktop render/export app first.
2. Define a portable chop kit export format.
3. Plan a later VST/AU plugin that loads prepared chop kits and plays them from
   MIDI in a DAW.

Do not try to turn the current Python batch renderer directly into a real-time
VST. Heavy analysis should happen in the desktop app. The future plugin should
focus on low-latency playback of prepared kits.

## Non-Negotiable Constraints

- Do not include private MIDI generation code.
- Do not require or name any copyrighted source sample as part of the public
  product.
- Do not commit source samples, generated chops, private MIDI files, or local
  render folders.
- Keep the command-line workflow working while adding app-oriented structure.
- Make random or varied render behavior deterministic when a seed is provided.
- Keep all exported manifests explicit enough that every rendered note can be
  traced back to its chosen chop, pitch shift, playback mode, and variation
  settings.

## Desktop App V1

Build the first product as a **macOS desktop render/export app**.

Recommended implementation path:

- Refactor the existing Python script into a reusable sampler engine.
- Keep a thin CLI wrapper for terminal users.
- Add a desktop GUI with PySide6 for fastest compatibility with the existing
  Python audio stack.
- Package the app with PyInstaller into a macOS `.app`, then wrap it in a `.dmg`
  for distribution.

The app should let users:

- Select a local WAV or AIFF sample.
- Select a local MIDI file.
- Choose the target MIDI track.
- Choose bar start and bar count.
- Configure chop detection:
  - minimum chop length
  - maximum chop length
  - onset threshold
  - maximum number of chops
- Configure pitch matching:
  - maximum pitch shift in semitones
  - exact-match preference
  - repeated-note variation behavior
- Configure playback mode and sample style variation.
- Run analysis/render.
- See summary results:
  - render path
  - total chops
  - pitched chops
  - unpitched chops
  - MIDI events rendered
  - exact-match notes
  - pitch-shifted notes
  - weak or over-limit events
- Open/export the render folder.

The first app version is render/export focused. It does not need live MIDI input
or real-time performance.

## Playback Modes

Implement playback modes as explicit render behaviors. Every MIDI event must
record the chosen playback mode in the note event map.

Required modes:

- `one-shot`: trigger the full chop at MIDI note-on and ignore note-off.
- `gated`: trigger at note-on and stop at note-off using a short release fade.
- `loop-forward`: loop the chop forward until note-off.
- `loop-forward-reverse`: play the chop forward, then reverse, repeating as a
  ping-pong loop until note-off.
- `loop-reverse-forward`: play the chop in reverse first, then forward,
  repeating as a reverse-first ping-pong loop until note-off.

Future modes:

- `stretch`: time-stretch the chop to the MIDI note duration.
- `slice-sequence`: step through chops in order regardless of pitch.

Loop modes must avoid clicks by using short crossfades or edge fades. Gated and
looped modes must respect MIDI note duration. One-shot mode must start exactly
at MIDI note-on and may overlap later notes.

## Varied Sample Style Modes

Add style modes that can vary chop selection, playback mode, and performance
details per MIDI trigger. Every event must write its resolved choices to the
event map.

Required style modes:

- `fixed`: every MIDI event uses the selected playback mode and normal chop
  selection.
- `round-robin`: repeated notes rotate through compatible chops for the target
  note.
- `random-chop`: each trigger randomly selects from compatible chops for the
  target note.
- `random-playback`: each trigger randomly selects from enabled playback modes.
- `weighted-random`: each trigger selects playback mode using user-defined
  probability weights.
- `velocity-style`: MIDI velocity chooses playback behavior.
- `note-range-style`: low, mid, and high MIDI ranges use different playback
  modes.
- `alternating-style`: events cycle through a configured playback mode list.
- `humanized-style`: each trigger may vary chop choice, start offset, gain, pan,
  pitch cents, and playback mode within user-defined limits.

Default behavior:

- Use `fixed` style mode by default.
- Use `one-shot` playback by default.
- Use deterministic random choices when a seed is supplied.
- Do not allow humanization to move a chop before its MIDI note-on time unless
  the user explicitly enables negative timing offsets.

## Future Chop Kit Format

Define a portable chop kit export format so the desktop app can prepare material
for a later DAW plugin.

The kit should contain:

- normalized chop WAV files
- original sample metadata, excluding copyrighted audio unless the user exports
  it intentionally
- pitch analysis per chop
- MIDI note mapping
- compatible playback modes
- loop points or loop render settings where applicable
- round-robin groups
- variation rules
- versioned JSON manifest

The manifest must be stable enough for a future plugin to load without running
onset detection or pitch analysis in the DAW.

## VST/AU Plugin Roadmap

Treat the VST/AU plugin as a later product, not a direct wrapper around the
Python app.

Recommended plugin architecture:

- Build the plugin in JUCE or iPlug2.
- Load prepared chop kits exported by the desktop app.
- Respond to MIDI note-on/note-off inside the DAW.
- Perform low-latency sample playback.
- Support one-shot, gated, loop-forward, forward-reverse, and reverse-forward
  playback.
- Support round-robin and deterministic variation rules.
- Expose automatable parameters for playback mode, style mode, pitch shift
  range, loop behavior, release, humanization amount, and output gain.
- Keep all heavy analysis outside the plugin audio thread.

The plugin should not run librosa, onset detection, or full pitch analysis in
real time.

## Implementation Requirements

Restructure the code so app and CLI share the same engine:

- Introduce a typed render configuration object.
- Introduce a typed render result object.
- Move command-line parsing away from the core audio logic.
- Keep exported file names stable.
- Preserve current report outputs while adding playback/style fields.
- Keep all generated output in ignored local output folders unless explicitly
  exporting demo-safe artifacts.

The app should handle common errors clearly:

- missing sample file
- missing MIDI file
- unsupported audio format
- no MIDI events in selected range
- no pitched chops detected
- no compatible chops within pitch-shift limits
- failed render/export

## Testing Requirements

Add tests or repeatable smoke checks for:

- existing CLI render behavior
- required output files
- MIDI note-on alignment
- one-shot playback
- gated playback ending at note-off with fade
- loop-forward duration matching note duration
- forward-reverse loop continuity
- reverse-forward loop continuity
- deterministic seeded random style behavior
- event map completeness for every rendered MIDI event
- app packaging launch on macOS

Manual acceptance checks should include:

- Compare the rendered microchop WAV against the reference MIDI/WAV.
- Verify each note starts at the MIDI note-on time.
- Verify varied style modes actually produce different per-trigger choices.
- Verify render reports expose enough detail to debug pitch mismatches.
- Verify the app can run without a manually activated development virtual
  environment.

## Acceptance Criteria

The implementation is complete when:

- The CLI still renders a WAV from a user-provided sample and MIDI file.
- The desktop app can render the same output through a GUI.
- The app exports render WAV, reference MIDI, reference WAV, chop manifest,
  event map, coverage report, and summary.
- Playback modes are selectable and recorded per event.
- Varied sample style modes can choose different playback modes per trigger.
- Seeded variation produces repeatable renders.
- Public repository contents exclude private MIDI generation code, source
  samples, generated chops, and local render folders.
- Documentation explains desktop app first and VST/AU plugin later.

## Expected Output From The LLM

When implementing this prompt, provide:

- A concise implementation summary.
- Files changed.
- Any backup files created.
- Commands run for verification.
- Known limitations or deferred plugin work.
- Clear instructions for launching the app and running the CLI.
