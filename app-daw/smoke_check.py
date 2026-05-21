#!/usr/bin/env python3
"""Self-contained app/DAW implementation smoke checks.

This creates a synthetic sample and MIDI file in a temp directory, then verifies
the shared render engine without relying on private source assets.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from microchop_sampler import RenderConfig, render_job


def write_synthetic_sample(path: Path, sr: int = 22050) -> None:
    notes = [261.63, 329.63, 392.0, 440.0, 493.88, 523.25]
    parts = []
    silence = np.zeros(int(sr * 0.05), dtype=np.float32)
    for freq in notes:
        length = int(sr * 0.18)
        t = np.arange(length, dtype=np.float32) / sr
        tone = 0.45 * np.sin(2.0 * math.pi * freq * t)
        fade = min(int(sr * 0.01), length // 2)
        tone[:fade] *= np.linspace(0.0, 1.0, fade, dtype=np.float32)
        tone[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
        parts.extend([silence, tone.astype(np.float32)])
    audio = np.concatenate(parts)
    sf.write(path, np.stack([audio, audio], axis=1), sr)


def write_synthetic_midi(path: Path) -> None:
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    meta.append(mido.MetaMessage("end_of_track", time=0))
    mid.tracks.append(meta)

    track = mido.MidiTrack()
    track.name = "Main Melody"
    track.append(mido.MetaMessage("track_name", name="Main Melody", time=0))
    last_tick = 0
    for tick, note in [(0, 60), (240, 64), (480, 67), (720, 69)]:
        track.append(mido.Message("note_on", note=note, velocity=96, time=tick - last_tick))
        track.append(mido.Message("note_off", note=note, velocity=0, time=180))
        last_tick = tick + 180
    track.append(mido.MetaMessage("end_of_track", time=1920 - last_tick))
    mid.tracks.append(track)
    mid.save(path)


def assert_render(config: RenderConfig) -> list[dict[str, object]]:
    result = render_job(config)
    data = asdict(result)
    required = [
        data["render"],
        data["reference_midi"],
        data["reference_wav"],
        str(Path(data["run_dir"]) / "manifests" / "chops.json"),
        str(Path(data["run_dir"]) / "renders" / "note_event_map.json"),
        str(Path(data["run_dir"]) / "reports" / "coverage_report.json"),
        str(Path(data["run_dir"]) / "reports" / "summary.md"),
    ]
    missing = [path for path in required if not Path(path).exists()]
    if missing:
        raise AssertionError(f"Missing expected outputs: {missing}")
    event_map = json.loads((Path(data["run_dir"]) / "renders" / "note_event_map.json").read_text())
    if len(event_map) != data["midi_events"]:
        raise AssertionError("Event map length does not match rendered MIDI events")
    for event in event_map:
        for key in ("playback_mode", "style_mode", "selected_chop_id", "render_start_sec", "render_duration_sec"):
            if key not in event:
                raise AssertionError(f"Event missing {key}: {event}")
    return event_map


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="dilla-microchop-smoke-") as tmp:
        root = Path(tmp)
        sample = root / "synthetic_sample.wav"
        midi = root / "synthetic.mid"
        write_synthetic_sample(sample)
        write_synthetic_midi(midi)

        fixed = assert_render(
            RenderConfig(
                sample=str(sample),
                midi=str(midi),
                bar_start=0,
                bar_count=1,
                playback_mode="gated",
                style_mode="fixed",
                max_chops=24,
                output_dir=str(root / "fixed"),
            )
        )
        if {event["playback_mode"] for event in fixed} != {"gated"}:
            raise AssertionError("Fixed gated render did not resolve to gated playback")

        random_a = assert_render(
            RenderConfig(
                sample=str(sample),
                midi=str(midi),
                bar_start=0,
                bar_count=1,
                playback_mode="one-shot",
                style_mode="random-playback",
                enabled_playback_modes="one-shot,gated,loop-forward",
                max_chops=24,
                seed=2026,
                output_dir=str(root / "random-a"),
            )
        )
        random_b = assert_render(
            RenderConfig(
                sample=str(sample),
                midi=str(midi),
                bar_start=0,
                bar_count=1,
                playback_mode="one-shot",
                style_mode="random-playback",
                enabled_playback_modes="one-shot,gated,loop-forward",
                max_chops=24,
                seed=2026,
                output_dir=str(root / "random-b"),
            )
        )
        if [event["playback_mode"] for event in random_a] != [event["playback_mode"] for event in random_b]:
            raise AssertionError("Seeded random playback mode choices are not deterministic")

        sliced = assert_render(
            RenderConfig(
                sample=str(sample),
                midi=str(midi),
                bar_start=0,
                bar_count=1,
                playback_mode="slice-sequence",
                style_mode="fixed",
                max_chops=24,
                output_dir=str(root / "slice"),
            )
        )
        if [event["selected_chop_id"] for event in sliced] != list(range(len(sliced))):
            raise AssertionError("Slice sequence did not advance through chops")

        print("app-daw smoke checks passed")


if __name__ == "__main__":
    main()
