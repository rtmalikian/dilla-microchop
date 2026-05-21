# Implementation Log

- Added `microchop_midigen/` as an isolated MIDI-generation copy from
  `midigen_scripts/`.
- Added `microchop_midigen/generate_midi_only.py` to call only the copied
  MIDI generator.
- Added `microchop_sampler.py` for chopping, pitch labeling, MIDI phrase
  extraction, one-shot rendering, and reports.
- Added `microchop_requirements.txt` with focused audio/MIDI dependencies.
- Added `README.md` with setup and proof-render commands.
- No existing source files were modified; `midigen_scripts/` was left intact.
- 2026-05-21: Backed up `microchop_sampler.py`, `README.md`, and this log to
  `backups/20260521_reference_render/` before adding 8-bar reference MIDI and
  diagnostic WAV outputs for direct comparison with the microchop render.
- 2026-05-21: Backed up `README.md` and this log to
  `backups/20260521_youtube_readme/` before adding the YouTube walkthrough
  thumbnail link to the GitHub README.
- 2026-05-21: Backed up `.gitignore`, `README.md`, and this log to
  `backups/20260521_public_demo_artifacts/` before allowing only the public
  Ableton analysis file and final microchop render under `demo_artifacts/`.
- 2026-05-21: Backed up `README.md` and this log to
  `backups/20260521_readme_rights_cleanup/` before removing the named local
  proof sample path from the README and replacing the YouTube thumbnail with a
  plain external walkthrough link.
- 2026-05-21: Backed up `microchop_sampler.py`, `README.md`, `.gitignore`, and
  this log to `backups/20260521_remove_private_midigen/` before removing the
  private MIDI generation code from GitHub and changing the public workflow to
  bring-your-own MIDI.
- 2026-05-21: Backed up this log to `backups/20260521_app_daw_prompt/` before
  adding `app-daw/LLM_PROMPT.md` with the desktop app and future DAW plugin
  implementation prompt.
- 2026-05-21: Backed up `microchop_sampler.py`, `microchop_requirements.txt`,
  `README.md`, `.gitignore`, and this log to
  `backups/20260521_app_daw_implementation/` before implementing the shared
  render entry point, desktop app wrapper, playback/style mode expansion, and
  app packaging documentation.
