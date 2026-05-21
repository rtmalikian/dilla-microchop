#!/usr/bin/env python3
"""MIDI-only entrypoint for the isolated microchop generator copy."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from midi_orchestrator import main as generate_midi


def generate(output_dir: str | None = None) -> tuple[str, dict]:
    result = generate_midi()
    if isinstance(result, tuple):
        midi_path, metadata = result
    else:
        midi_path, metadata = result, {}

    if output_dir:
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        copied = target_dir / Path(midi_path).name
        shutil.copy2(midi_path, copied)
        midi_path = str(copied)

        meta_path = copied.with_suffix(".metadata.json")
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

    return midi_path, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate MIDI only for microchop POC")
    parser.add_argument("--output-dir", default=None, help="Optional directory to copy MIDI into")
    args = parser.parse_args()
    midi_path, metadata = generate(args.output_dir)
    print(json.dumps({"midi_path": midi_path, "metadata": metadata}, indent=2))


if __name__ == "__main__":
    main()
