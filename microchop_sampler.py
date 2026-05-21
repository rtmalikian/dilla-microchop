#!/usr/bin/env python3
"""Render a MIDI phrase with tuned microchops."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import librosa
import mido
import numpy as np
import soundfile as sf


PLAYBACK_MODES = [
    "one-shot",
    "gated",
    "loop-forward",
    "loop-forward-reverse",
    "loop-reverse-forward",
    "stretch",
    "slice-sequence",
]

STYLE_MODES = [
    "fixed",
    "round-robin",
    "random-chop",
    "random-playback",
    "weighted-random",
    "velocity-style",
    "note-range-style",
    "alternating-style",
    "humanized-style",
]


@dataclass
class MidiNoteEvent:
    index: int
    start_tick: int
    end_tick: int
    start_sec: float
    duration_sec: float
    note: int
    velocity: int
    channel: int


@dataclass
class RenderConfig:
    sample: str = ""
    midi: str = ""
    target_track: str = "Main Melody"
    bar_start: int = 8
    bar_count: int = 8
    playback_mode: str = "one-shot"
    style_mode: str = "fixed"
    enabled_playback_modes: str = "one-shot,gated,loop-forward,loop-forward-reverse,loop-reverse-forward"
    weighted_playback_modes: str = ""
    alternating_playback_modes: str = "one-shot,gated,loop-forward"
    low_note_max: int = 59
    high_note_min: int = 72
    low_playback_mode: str = "loop-forward"
    mid_playback_mode: str = "gated"
    high_playback_mode: str = "one-shot"
    soft_velocity_max: int = 55
    hard_velocity_min: int = 100
    soft_playback_mode: str = "gated"
    medium_playback_mode: str = "loop-forward"
    hard_playback_mode: str = "one-shot"
    min_chop_ms: float = 45.0
    max_chop_ms: float = 260.0
    onset_threshold: float = 0.08
    max_pitch_shift_semitones: float = 12.0
    chops_per_note: int = 8
    max_chops: int = 256
    seed: int = 1337
    output_dir: str | None = None
    release_ms: float = 8.0
    loop_crossfade_ms: float = 5.0
    humanize_start_ms: float = 8.0
    humanize_gain_db: float = 1.5
    humanize_pan: float = 0.15
    humanize_pitch_cents: float = 8.0
    allow_negative_humanize: bool = False


@dataclass
class RenderResult:
    run_dir: str
    midi: str
    render: str
    reference_midi: str
    reference_wav: str
    chops: int
    pitched_chops: int
    midi_events: int
    peak_dbfs: float


def note_name(midi_note: int) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[midi_note % 12]}{midi_note // 12 - 1}"


def hz_to_midi(freq: float) -> float:
    return 69.0 + 12.0 * math.log2(freq / 440.0)


def midi_to_hz(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


def db_peak(audio: np.ndarray) -> float:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    return -120.0 if peak <= 1e-9 else 20.0 * math.log10(peak)


def ensure_stereo_shape(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio[:, None]
    if audio.shape[0] <= 8 and audio.shape[0] < audio.shape[-1]:
        return audio.T
    return audio


def mono_for_analysis(audio: np.ndarray) -> np.ndarray:
    audio = ensure_stereo_shape(audio)
    return np.mean(audio, axis=1)


def apply_fades(audio: np.ndarray, sr: int, fade_ms: float = 4.0) -> np.ndarray:
    out = np.array(audio, dtype=np.float32, copy=True)
    if out.size == 0:
        return out
    fade_len = min(int(sr * fade_ms / 1000.0), max(1, out.shape[0] // 2))
    fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
    fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
    out[:fade_len] *= fade_in[:, None]
    out[-fade_len:] *= fade_out[:, None]
    return out


def apply_release_fade(audio: np.ndarray, sr: int, release_ms: float) -> np.ndarray:
    out = np.array(audio, dtype=np.float32, copy=True)
    if out.size == 0:
        return out
    fade_len = min(int(sr * release_ms / 1000.0), max(1, out.shape[0]))
    out[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)[:, None]
    return out


def equal_power_pan(audio: np.ndarray, pan: float) -> np.ndarray:
    if audio.shape[1] < 2 or abs(pan) < 1e-6:
        return audio
    pan = max(-1.0, min(1.0, float(pan)))
    angle = (pan + 1.0) * (math.pi / 4.0)
    out = np.array(audio, dtype=np.float32, copy=True)
    out[:, 0] *= math.cos(angle) * math.sqrt(2.0)
    out[:, 1] *= math.sin(angle) * math.sqrt(2.0)
    return out


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def safe_render_stem(track_name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "_", track_name.lower()).strip("_")
    return stem or "track"


def parse_weighted_modes(value: str) -> list[tuple[str, float]]:
    weighted: list[tuple[str, float]] = []
    for item in parse_csv(value):
        if ":" not in item:
            weighted.append((item, 1.0))
            continue
        mode, weight = item.split(":", 1)
        try:
            parsed = max(0.0, float(weight))
        except ValueError:
            parsed = 1.0
        weighted.append((mode.strip(), parsed))
    return [(mode, weight) for mode, weight in weighted if mode and weight > 0.0]


def weighted_choice(rng: random.Random, weighted: list[tuple[str, float]], fallback: str) -> str:
    if not weighted:
        return fallback
    total = sum(weight for _mode, weight in weighted)
    if total <= 0.0:
        return fallback
    pick = rng.uniform(0.0, total)
    cursor = 0.0
    for mode, weight in weighted:
        cursor += weight
        if pick <= cursor:
            return mode
    return weighted[-1][0]


def stretch_or_trim(audio: np.ndarray, target_len: int) -> np.ndarray:
    if target_len <= 0:
        return audio[:0]
    if audio.shape[0] == target_len:
        return audio
    if audio.shape[0] <= 1:
        return np.zeros((target_len, audio.shape[1]), dtype=np.float32)
    src_x = np.linspace(0.0, 1.0, audio.shape[0], dtype=np.float32)
    dst_x = np.linspace(0.0, 1.0, target_len, dtype=np.float32)
    channels = [np.interp(dst_x, src_x, audio[:, ch]).astype(np.float32) for ch in range(audio.shape[1])]
    return np.stack(channels, axis=1)


def loop_audio(audio: np.ndarray, target_len: int, mode: str, sr: int, crossfade_ms: float) -> np.ndarray:
    if target_len <= 0:
        return audio[:0]
    if audio.size == 0:
        return np.zeros((target_len, 1), dtype=np.float32)
    if mode == "loop-forward":
        cycle = audio
    elif mode == "loop-forward-reverse":
        cycle = np.vstack([audio, audio[::-1]])
    elif mode == "loop-reverse-forward":
        cycle = np.vstack([audio[::-1], audio])
    else:
        cycle = audio
    repeats = int(math.ceil(target_len / max(1, cycle.shape[0])))
    rendered = np.tile(cycle, (repeats, 1))[:target_len]
    crossfade_len = min(int(sr * crossfade_ms / 1000.0), max(0, rendered.shape[0] // 8))
    if crossfade_len > 1:
        rendered = apply_fades(rendered, sr, crossfade_ms)
    return rendered.astype(np.float32)


def conservative_normalize(audio: np.ndarray, target_peak: float = 0.82) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak <= 1e-9:
        return audio.astype(np.float32)
    if peak > target_peak:
        audio = audio * (target_peak / peak)
    return audio.astype(np.float32)


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    audio, sr = librosa.load(path, sr=None, mono=False)
    return ensure_stereo_shape(audio).astype(np.float32), int(sr)


def split_segments(
    mono: np.ndarray,
    sr: int,
    min_ms: float,
    max_ms: float,
    onset_delta: float,
) -> list[tuple[int, int]]:
    onset_frames = librosa.onset.onset_detect(
        y=mono,
        sr=sr,
        units="samples",
        backtrack=True,
        delta=onset_delta,
        wait=1,
    )
    starts = sorted({0, *[int(s) for s in onset_frames if 0 <= int(s) < len(mono)]})
    min_len = max(1, int(sr * min_ms / 1000.0))
    max_len = max(min_len, int(sr * max_ms / 1000.0))
    segments: list[tuple[int, int]] = []

    for idx, start in enumerate(starts):
        next_start = starts[idx + 1] if idx + 1 < len(starts) else len(mono)
        end = min(next_start, start + max_len, len(mono))
        if end - start >= min_len:
            segments.append((start, end))

    return segments


def estimate_pitch(chop_mono: np.ndarray, sr: int) -> dict[str, Any]:
    if len(chop_mono) < int(sr * 0.035):
        return {"pitched": False, "reason": "too_short"}

    y = chop_mono.astype(np.float32)
    if float(np.max(np.abs(y))) <= 1e-5:
        return {"pitched": False, "reason": "near_silent"}

    frame_length = 1024 if len(y) < 2048 else 2048
    y_pad = y
    if len(y_pad) < frame_length:
        y_pad = np.pad(y_pad, (0, frame_length - len(y_pad)))

    try:
        f0_yin = librosa.yin(
            y_pad,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=sr,
            frame_length=frame_length,
        )
        f0_yin = f0_yin[np.isfinite(f0_yin)]
        if len(f0_yin) > 0:
            freq = float(np.nanmedian(f0_yin))
            midi_series = 69.0 + 12.0 * np.log2(f0_yin / 440.0)
            spread = float(np.nanstd(midi_series))
            confidence = max(0.0, min(1.0, 1.0 - (spread / 2.5)))
            if confidence < 0.18:
                return {
                    "pitched": False,
                    "reason": "unstable_f0",
                    "confidence": confidence,
                    "pitch_method": "yin",
                }
            midi_float = hz_to_midi(freq)
            midi_note = int(round(midi_float))
            return {
                "pitched": True,
                "f0_hz": freq,
                "midi_note": midi_note,
                "note_name": note_name(midi_note),
                "cents_offset": float((midi_float - midi_note) * 100.0),
                "confidence": confidence,
                "voiced_ratio": 0.0,
                "pitch_method": "yin",
            }
    except Exception as exc:
        return {"pitched": False, "reason": "pitch_error", "error": str(exc)}

    return {"pitched": False, "reason": "no_stable_f0"}


def make_chops(args: RenderConfig, run_dir: Path) -> list[dict[str, Any]]:
    source_audio, sr = load_audio(Path(args.sample))
    mono = mono_for_analysis(source_audio)
    segments = split_segments(mono, sr, args.min_chop_ms, args.max_chop_ms, args.onset_threshold)
    if args.max_chops and len(segments) > args.max_chops:
        segments = segments[: args.max_chops]
    chops_dir = run_dir / "chops"
    chops_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, Any]] = []
    for idx, (start, end) in enumerate(segments):
        chop = source_audio[start:end]
        chop = apply_fades(chop, sr)
        chop = conservative_normalize(chop)
        rel_path = Path("chops") / f"chop_{idx:04d}_{start}_{end}.wav"
        sf.write(run_dir / rel_path, chop, sr)

        chop_mono = mono_for_analysis(chop)
        pitch = estimate_pitch(chop_mono, sr)
        entry = {
            "id": idx,
            "path": str(rel_path),
            "source_start_sec": start / sr,
            "source_end_sec": end / sr,
            "duration_sec": (end - start) / sr,
            "rms": float(np.sqrt(np.mean(np.square(chop_mono)))) if chop_mono.size else 0.0,
            "peak": float(np.max(np.abs(chop))) if chop.size else 0.0,
            **pitch,
        }
        manifest.append(entry)

    manifest_dir = run_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "chops.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def copy_midi_into(midi_path: Path, run_dir: Path) -> Path:
    if not midi_path.exists():
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")
    midi_dir = run_dir / "midi"
    midi_dir.mkdir(parents=True, exist_ok=True)
    canonical = midi_dir / "input.mid"
    shutil.copy2(midi_path, canonical)
    return canonical


def tempo_segments(mid: mido.MidiFile) -> list[tuple[int, int]]:
    tempos: list[tuple[int, int]] = [(0, mido.bpm2tempo(120))]
    abs_tick = 0
    for msg in mid.tracks[0]:
        abs_tick += msg.time
        if msg.type == "set_tempo":
            tempos.append((abs_tick, msg.tempo))
    return sorted(tempos, key=lambda x: x[0])


def tick_to_seconds(tick: int, tempo_map: list[tuple[int, int]], ticks_per_beat: int) -> float:
    seconds = 0.0
    for idx, (start_tick, tempo) in enumerate(tempo_map):
        next_tick = tempo_map[idx + 1][0] if idx + 1 < len(tempo_map) else tick
        if tick <= start_tick:
            break
        span_end = min(tick, next_tick)
        if span_end > start_tick:
            seconds += mido.tick2second(span_end - start_tick, ticks_per_beat, tempo)
        if tick < next_tick:
            break
    return float(seconds)


def get_time_signature(mid: mido.MidiFile) -> tuple[int, int]:
    for track in mid.tracks:
        for msg in track:
            if msg.type == "time_signature":
                return int(msg.numerator), int(msg.denominator)
    return 4, 4


def track_name(track: mido.MidiTrack) -> str:
    if getattr(track, "name", None):
        return str(track.name)
    for msg in track:
        if msg.type == "track_name":
            return str(msg.name)
    return ""


def find_target_track(mid: mido.MidiFile, target_name: str) -> tuple[int, mido.MidiTrack, str | None]:
    names = [(idx, track_name(track), track) for idx, track in enumerate(mid.tracks)]
    for idx, name, track in names:
        if name == target_name:
            return idx, track, None
    for idx, name, track in names:
        if target_name.lower() in name.lower():
            return idx, track, f"Exact track '{target_name}' not found; using partial match '{name}'."
    if len(mid.tracks) > 2:
        return 2, mid.tracks[2], f"Track '{target_name}' not found; falling back to MIDI track index 2."
    raise RuntimeError(f"Track '{target_name}' not found and MIDI has no usable fallback track.")


def extract_midi_events(midi_path: Path, target_track: str, bar_start: int, bar_count: int) -> tuple[list[MidiNoteEvent], dict[str, Any]]:
    mid = mido.MidiFile(midi_path)
    numerator, denominator = get_time_signature(mid)
    ticks_per_bar = int(mid.ticks_per_beat * numerator * (4 / denominator))
    start_tick = int(bar_start * ticks_per_bar)
    end_tick = int((bar_start + bar_count) * ticks_per_bar)
    tempo_map = tempo_segments(mid)
    track_idx, track, warning = find_target_track(mid, target_track)

    active: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    events: list[MidiNoteEvent] = []
    abs_tick = 0
    for msg in track:
        abs_tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            active[(msg.channel, msg.note)].append((abs_tick, msg.velocity))
        elif msg.type in ("note_off", "note_on"):
            key = (getattr(msg, "channel", 0), msg.note)
            if active.get(key):
                note_start, velocity = active[key].pop(0)
                note_end = abs_tick
                if note_start >= start_tick and note_start < end_tick:
                    clipped_end = max(note_start + 1, min(note_end, end_tick))
                    start_sec = tick_to_seconds(note_start - start_tick, tempo_map, mid.ticks_per_beat)
                    end_sec = tick_to_seconds(clipped_end - start_tick, tempo_map, mid.ticks_per_beat)
                    events.append(
                        MidiNoteEvent(
                            index=len(events),
                            start_tick=note_start,
                            end_tick=clipped_end,
                            start_sec=start_sec,
                            duration_sec=max(0.001, end_sec - start_sec),
                            note=int(msg.note),
                            velocity=int(velocity),
                            channel=int(getattr(msg, "channel", 0)),
                        )
                    )

    info = {
        "ticks_per_beat": mid.ticks_per_beat,
        "time_signature": f"{numerator}/{denominator}",
        "ticks_per_bar": ticks_per_bar,
        "bar_start": bar_start,
        "bar_count": bar_count,
        "target_track": target_track,
        "selected_track_index": track_idx,
        "selected_track_name": track_name(track),
        "warning": warning,
    }
    return events, info


def tempo_from_midi(midi_path: Path) -> int:
    mid = mido.MidiFile(midi_path)
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return int(msg.tempo)
    return int(mido.bpm2tempo(120))


def render_reference_outputs(
    run_dir: Path,
    args: RenderConfig,
    midi_events: list[MidiNoteEvent],
    midi_info: dict[str, Any],
    midi_path: Path,
    sample_rate: int,
    channels: int,
) -> dict[str, Any]:
    renders_dir = run_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.target_track.lower().replace(' ', '_')}_bars_{args.bar_start}_{args.bar_start + args.bar_count}"
    midi_out = renders_dir / f"{stem}_reference.mid"
    wav_out = renders_dir / f"{stem}_reference.wav"

    tempo = tempo_from_midi(midi_path)
    numerator, denominator = (int(v) for v in midi_info["time_signature"].split("/", 1))
    ticks_per_beat = int(midi_info["ticks_per_beat"])
    ticks_per_bar = int(midi_info["ticks_per_bar"])
    excerpt_ticks = int(args.bar_count * ticks_per_bar)

    ref_mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    meta_track = mido.MidiTrack()
    meta_track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    meta_track.append(mido.MetaMessage("time_signature", numerator=numerator, denominator=denominator, time=0))
    meta_track.append(mido.MetaMessage("end_of_track", time=excerpt_ticks))
    ref_mid.tracks.append(meta_track)

    note_track = mido.MidiTrack()
    note_track.name = f"{args.target_track} bars {args.bar_start}-{args.bar_start + args.bar_count}"
    note_track.append(mido.MetaMessage("track_name", name=note_track.name, time=0))
    midi_messages: list[tuple[int, mido.Message]] = []
    start_tick_offset = int(args.bar_start * ticks_per_bar)
    for event in midi_events:
        rel_start = max(0, int(event.start_tick - start_tick_offset))
        rel_end = max(rel_start + 1, int(event.end_tick - start_tick_offset))
        midi_messages.append((
            rel_start,
            mido.Message("note_on", note=event.note, velocity=event.velocity, channel=event.channel, time=0),
        ))
        midi_messages.append((
            rel_end,
            mido.Message("note_off", note=event.note, velocity=0, channel=event.channel, time=0),
        ))
    last_tick = 0
    for tick, msg in sorted(midi_messages, key=lambda item: (item[0], item[1].type == "note_on")):
        msg.time = max(0, tick - last_tick)
        note_track.append(msg)
        last_tick = tick
    note_track.append(mido.MetaMessage("end_of_track", time=max(0, excerpt_ticks - last_tick)))
    ref_mid.tracks.append(note_track)
    ref_mid.save(midi_out)

    duration = float(mido.tick2second(excerpt_ticks, ticks_per_beat, tempo))
    audio = np.zeros((max(1, int(math.ceil(duration * sample_rate))), channels), dtype=np.float32)
    for event in midi_events:
        start = int(round(event.start_sec * sample_rate))
        length = max(1, int(round(event.duration_sec * sample_rate)))
        end = min(audio.shape[0], start + length)
        if end <= start:
            continue
        t = np.arange(end - start, dtype=np.float32) / float(sample_rate)
        freq = midi_to_hz(event.note)
        sine = np.sin(2.0 * np.pi * freq * t)
        triangle = (2.0 / np.pi) * np.arcsin(sine)
        tone = (0.18 * (event.velocity / 127.0) * triangle).astype(np.float32)
        fade_len = min(int(sample_rate * 0.004), max(1, len(tone) // 2))
        tone[:fade_len] *= np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        tone[-fade_len:] *= np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
        audio[start:end] += tone[:, None]
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.95:
        audio *= 0.95 / peak
    sf.write(wav_out, audio, sample_rate)

    return {
        "reference_midi": str(midi_out),
        "reference_wav": str(wav_out),
        "reference_note_events": len(midi_events),
        "reference_duration_sec": float(audio.shape[0] / sample_rate),
        "reference_peak": float(np.max(np.abs(audio))) if audio.size else 0.0,
        "reference_peak_dbfs": db_peak(audio),
    }


def build_chop_index(chops: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    index: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for chop in chops:
        if chop.get("pitched") and isinstance(chop.get("midi_note"), int):
            index[int(chop["midi_note"])].append(chop)
    for note in index:
        index[note].sort(key=lambda c: (-float(c.get("confidence", 0.0)), c["id"]))
    return index


def choose_chop(
    target_note: int,
    chop_index: dict[int, list[dict[str, Any]]],
    counters: dict[int, int],
    max_shift: float,
    style_mode: str = "fixed",
    rng: random.Random | None = None,
) -> tuple[dict[str, Any], int, bool, bool]:
    if not chop_index:
        raise RuntimeError("No pitched chops available for rendering.")
    available = sorted(chop_index.keys(), key=lambda n: (abs(n - target_note), n))
    exact = target_note in chop_index
    chosen_note = target_note if exact else available[0]
    shift = int(target_note - chosen_note)
    over_limit = abs(shift) > max_shift
    choices = chop_index[chosen_note]
    if style_mode == "random-chop" and rng is not None:
        idx = rng.randrange(len(choices))
    else:
        idx = counters[target_note] % len(choices)
    counters[target_note] += 1
    return choices[idx], shift, exact, over_limit


def resolve_playback_mode(
    args: RenderConfig,
    event: MidiNoteEvent,
    event_ordinal: int,
    rng: random.Random,
) -> str:
    base = args.playback_mode
    style = args.style_mode
    if style in ("fixed", "round-robin", "random-chop"):
        return base
    if style == "random-playback":
        return rng.choice(parse_csv(args.enabled_playback_modes) or [base])
    if style == "weighted-random":
        return weighted_choice(rng, parse_weighted_modes(args.weighted_playback_modes), base)
    if style == "velocity-style":
        if event.velocity <= args.soft_velocity_max:
            return args.soft_playback_mode
        if event.velocity >= args.hard_velocity_min:
            return args.hard_playback_mode
        return args.medium_playback_mode
    if style == "note-range-style":
        if event.note <= args.low_note_max:
            return args.low_playback_mode
        if event.note >= args.high_note_min:
            return args.high_playback_mode
        return args.mid_playback_mode
    if style == "alternating-style":
        modes = parse_csv(args.alternating_playback_modes) or [base]
        return modes[event_ordinal % len(modes)]
    if style == "humanized-style":
        return rng.choice(parse_csv(args.enabled_playback_modes) or [base])
    return base


def render_chop_for_event(
    chop_audio: np.ndarray,
    event: MidiNoteEvent,
    playback_mode: str,
    sr: int,
    args: RenderConfig,
) -> np.ndarray:
    target_len = max(1, int(round(event.duration_sec * sr)))
    if playback_mode == "one-shot":
        return chop_audio
    if playback_mode == "gated":
        return apply_release_fade(chop_audio[:target_len], sr, args.release_ms)
    if playback_mode in ("loop-forward", "loop-forward-reverse", "loop-reverse-forward"):
        looped = loop_audio(chop_audio, target_len, playback_mode, sr, args.loop_crossfade_ms)
        return apply_release_fade(looped, sr, args.release_ms)
    if playback_mode == "stretch":
        return apply_release_fade(stretch_or_trim(chop_audio, target_len), sr, args.release_ms)
    if playback_mode == "slice-sequence":
        return chop_audio
    raise ValueError(f"Unsupported playback mode: {playback_mode}")


def humanize_event_audio(
    audio: np.ndarray,
    event: MidiNoteEvent,
    args: RenderConfig,
    rng: random.Random,
) -> tuple[np.ndarray, float, float, float]:
    if args.style_mode != "humanized-style":
        return audio, 0.0, 0.0, 0.0
    start_ms = rng.uniform(-args.humanize_start_ms if args.allow_negative_humanize else 0.0, args.humanize_start_ms)
    gain_db = rng.uniform(-args.humanize_gain_db, args.humanize_gain_db)
    pan = rng.uniform(-args.humanize_pan, args.humanize_pan)
    out = np.array(audio, dtype=np.float32, copy=True)
    out *= float(10.0 ** (gain_db / 20.0))
    out = equal_power_pan(out, pan)
    return out, start_ms, gain_db, pan


def pitch_shift_audio(audio: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    if abs(semitones) < 1e-6:
        return audio
    shifted_channels = [
        librosa.effects.pitch_shift(y=audio[:, ch], sr=sr, n_steps=semitones)
        for ch in range(audio.shape[1])
    ]
    min_len = min(len(ch) for ch in shifted_channels)
    return np.stack([ch[:min_len] for ch in shifted_channels], axis=1).astype(np.float32)


def render_events(
    args: RenderConfig,
    run_dir: Path,
    midi_events: list[MidiNoteEvent],
    chops: list[dict[str, Any]],
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    source_audio, sr = load_audio(Path(args.sample))
    source_channels = source_audio.shape[1]
    chop_index = build_chop_index(chops)
    counters: dict[int, int] = defaultdict(int)
    rendered_map: list[dict[str, Any]] = []
    rng = random.Random(args.seed)

    if not midi_events:
        raise RuntimeError("No MIDI note events found in requested track/bar range.")
    if not chops:
        raise RuntimeError("No chops were detected; cannot render microchop sampler.")
    if not chop_index and args.playback_mode != "slice-sequence" and args.style_mode != "random-playback":
        raise RuntimeError("No pitched chops were detected; cannot render pitched microchop sampler.")

    output_len = int((max(e.start_sec for e in midi_events) + 4.0) * sr)
    mix = np.zeros((output_len, source_channels), dtype=np.float32)

    for event in midi_events:
        playback_mode = resolve_playback_mode(args, event, len(rendered_map), rng)
        if playback_mode == "slice-sequence":
            chop_meta = chops[len(rendered_map) % len(chops)]
            source_note = chop_meta.get("midi_note")
            shift = int(event.note - source_note) if isinstance(source_note, int) else 0
            exact = bool(isinstance(source_note, int) and source_note == event.note)
            over_limit = abs(shift) > args.max_pitch_shift_semitones
        else:
            chop_style = "random-chop" if args.style_mode in ("random-chop", "humanized-style") else args.style_mode
            chop_meta, shift, exact, over_limit = choose_chop(
                event.note,
                chop_index,
                counters,
                args.max_pitch_shift_semitones,
                chop_style,
                rng,
            )
        start = int(round(chop_meta["source_start_sec"] * sr))
        end = int(round(chop_meta["source_end_sec"] * sr))
        chop_audio = np.array(source_audio[start:end], dtype=np.float32, copy=True)
        chop_audio = apply_fades(chop_audio, sr)
        chop_audio = pitch_shift_audio(chop_audio, sr, shift)
        humanize_pitch_cents = 0.0
        if args.style_mode == "humanized-style":
            humanize_pitch_cents = rng.uniform(-args.humanize_pitch_cents, args.humanize_pitch_cents)
            chop_audio = pitch_shift_audio(chop_audio, sr, humanize_pitch_cents / 100.0)
        chop_audio = render_chop_for_event(chop_audio, event, playback_mode, sr, args)
        chop_audio, humanize_start_ms, humanize_gain_db, humanize_pan = humanize_event_audio(
            chop_audio,
            event,
            args,
            rng,
        )
        gain = (event.velocity / 127.0) ** 1.25
        chop_audio *= float(gain)
        insert = int(round((event.start_sec + humanize_start_ms / 1000.0) * sr))
        insert = max(0, insert)
        needed = insert + chop_audio.shape[0]
        if needed > mix.shape[0]:
            extra = np.zeros((needed - mix.shape[0], source_channels), dtype=np.float32)
            mix = np.vstack([mix, extra])
        mix[insert:needed] += chop_audio[:, :source_channels]
        rendered_map.append(
            {
                "event_index": event.index,
                "target_midi_note": event.note,
                "target_note_name": note_name(event.note),
                "velocity": event.velocity,
                "start_sec": event.start_sec,
                "midi_duration_sec": event.duration_sec,
                "selected_chop_id": chop_meta["id"],
                "selected_chop_path": chop_meta["path"],
                "source_midi_note": chop_meta.get("midi_note"),
                "source_note_name": chop_meta.get("note_name"),
                "pitch_shift_semitones": shift,
                "exact_match": exact,
                "over_pitch_shift_limit": over_limit,
                "playback_mode": playback_mode,
                "style_mode": args.style_mode,
                "render_start_sec": insert / sr,
                "render_duration_sec": chop_audio.shape[0] / sr,
                "humanize_start_ms": humanize_start_ms,
                "humanize_gain_db": humanize_gain_db,
                "humanize_pan": humanize_pan,
                "humanize_pitch_cents": humanize_pitch_cents,
            }
        )

    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    if peak > 0.98:
        mix *= 0.98 / peak
    non_silent = np.where(np.max(np.abs(mix), axis=1) > 1e-6)[0]
    if non_silent.size:
        tail = int(sr * 0.02)
        mix = mix[: min(mix.shape[0], int(non_silent[-1]) + tail)]
    renders_dir = run_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    render_path = renders_dir / f"{safe_render_stem(args.target_track)}_bars_{args.bar_start}_{args.bar_start + args.bar_count}_microchop.wav"
    sf.write(render_path, mix, sr)
    (renders_dir / "note_event_map.json").write_text(json.dumps(rendered_map, indent=2) + "\n")
    stats = {
        "sample_rate": sr,
        "channels": source_channels,
        "duration_sec": float(mix.shape[0] / sr),
        "peak": float(np.max(np.abs(mix))) if mix.size else 0.0,
        "peak_dbfs": db_peak(mix),
    }
    return render_path, rendered_map, stats


def write_reports(
    run_dir: Path,
    args: RenderConfig,
    chops: list[dict[str, Any]],
    midi_events: list[MidiNoteEvent],
    midi_info: dict[str, Any],
    event_map: list[dict[str, Any]],
    render_stats: dict[str, Any],
    reference_stats: dict[str, Any],
) -> None:
    reports_dir = run_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    pitched = [c for c in chops if c.get("pitched")]
    unpitched = [c for c in chops if not c.get("pitched")]
    required_notes = sorted({e.note for e in midi_events})
    available_notes = sorted({int(c["midi_note"]) for c in pitched if isinstance(c.get("midi_note"), int)})
    exact_notes = sorted({m["target_midi_note"] for m in event_map if m["exact_match"]})
    shifted_notes = sorted({m["target_midi_note"] for m in event_map if not m["exact_match"]})
    weak_events = [m for m in event_map if m["over_pitch_shift_limit"]]

    coverage = {
        "sample": args.sample,
        "midi_info": midi_info,
        "total_chops": len(chops),
        "pitched_chops": len(pitched),
        "unpitched_chops": len(unpitched),
        "required_midi_notes": [{"midi_note": n, "note_name": note_name(n)} for n in required_notes],
        "available_chop_notes": [{"midi_note": n, "note_name": note_name(n)} for n in available_notes],
        "exact_match_notes": [{"midi_note": n, "note_name": note_name(n)} for n in exact_notes],
        "pitch_shifted_notes": [{"midi_note": n, "note_name": note_name(n)} for n in shifted_notes],
        "weak_or_over_limit_events": weak_events,
        "render_stats": render_stats,
        "reference_outputs": reference_stats,
        "playback_mode": args.playback_mode,
        "style_mode": args.style_mode,
    }
    (reports_dir / "coverage_report.json").write_text(json.dumps(coverage, indent=2) + "\n")

    summary = [
        "# Microchop POC Summary",
        "",
        f"- Sample: `{args.sample}`",
        f"- MIDI track: `{midi_info.get('selected_track_name')}`",
        f"- Bars: {args.bar_start}-{args.bar_start + args.bar_count}",
        f"- Chops: {len(chops)} total, {len(pitched)} pitched, {len(unpitched)} unpitched",
        f"- MIDI note events rendered: {len(midi_events)}",
        f"- Required notes: {', '.join(note_name(n) for n in required_notes)}",
        f"- Exact-match notes: {', '.join(note_name(n) for n in exact_notes) or 'none'}",
        f"- Pitch-shifted notes: {', '.join(note_name(n) for n in shifted_notes) or 'none'}",
        f"- Weak/over-limit events: {len(weak_events)}",
        f"- Playback mode: `{args.playback_mode}`",
        f"- Style mode: `{args.style_mode}`",
        f"- Render duration: {render_stats['duration_sec']:.2f}s",
        f"- Render peak: {render_stats['peak']:.4f} ({render_stats['peak_dbfs']:.2f} dBFS)",
        f"- Reference MIDI: `{reference_stats['reference_midi']}`",
        f"- Reference WAV: `{reference_stats['reference_wav']}`",
        f"- Reference duration: {reference_stats['reference_duration_sec']:.2f}s",
    ]
    if midi_info.get("warning"):
        summary.append(f"- Warning: {midi_info['warning']}")
    summary.extend(
        [
            "",
            "Playback modes: `one-shot`, `gated`, `loop-forward`, `loop-forward-reverse`, `loop-reverse-forward`, `stretch`, and `slice-sequence`.",
            "",
        ]
    )
    (reports_dir / "summary.md").write_text("\n".join(summary))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render MIDI melody with tuned one-shot microchops")
    parser.add_argument("--sample", required=True, help="Path to the local WAV/AIFF sample to microchop")
    parser.add_argument("--midi", required=True, help="Path to the MIDI file whose melody track will trigger microchops")
    parser.add_argument("--target-track", default="Main Melody")
    parser.add_argument("--bar-start", type=int, default=8)
    parser.add_argument("--bar-count", type=int, default=8)
    parser.add_argument("--playback-mode", default="one-shot", choices=PLAYBACK_MODES)
    parser.add_argument("--style-mode", default="fixed", choices=STYLE_MODES)
    parser.add_argument("--enabled-playback-modes", default="one-shot,gated,loop-forward,loop-forward-reverse,loop-reverse-forward")
    parser.add_argument("--weighted-playback-modes", default="")
    parser.add_argument("--alternating-playback-modes", default="one-shot,gated,loop-forward")
    parser.add_argument("--low-note-max", type=int, default=59)
    parser.add_argument("--high-note-min", type=int, default=72)
    parser.add_argument("--low-playback-mode", default="loop-forward", choices=PLAYBACK_MODES)
    parser.add_argument("--mid-playback-mode", default="gated", choices=PLAYBACK_MODES)
    parser.add_argument("--high-playback-mode", default="one-shot", choices=PLAYBACK_MODES)
    parser.add_argument("--soft-velocity-max", type=int, default=55)
    parser.add_argument("--hard-velocity-min", type=int, default=100)
    parser.add_argument("--soft-playback-mode", default="gated", choices=PLAYBACK_MODES)
    parser.add_argument("--medium-playback-mode", default="loop-forward", choices=PLAYBACK_MODES)
    parser.add_argument("--hard-playback-mode", default="one-shot", choices=PLAYBACK_MODES)
    parser.add_argument("--min-chop-ms", type=float, default=45.0)
    parser.add_argument("--max-chop-ms", type=float, default=260.0)
    parser.add_argument("--onset-threshold", type=float, default=0.08)
    parser.add_argument("--max-pitch-shift-semitones", type=float, default=12.0)
    parser.add_argument("--chops-per-note", type=int, default=8)
    parser.add_argument("--max-chops", type=int, default=256)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--release-ms", type=float, default=8.0)
    parser.add_argument("--loop-crossfade-ms", type=float, default=5.0)
    parser.add_argument("--humanize-start-ms", type=float, default=8.0)
    parser.add_argument("--humanize-gain-db", type=float, default=1.5)
    parser.add_argument("--humanize-pan", type=float, default=0.15)
    parser.add_argument("--humanize-pitch-cents", type=float, default=8.0)
    parser.add_argument("--allow-negative-humanize", action="store_true", default=False)
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> RenderConfig:
    return RenderConfig(**vars(args))


def render_job(args: RenderConfig) -> RenderResult:
    random.seed(args.seed)
    np.random.seed(args.seed)

    run_dir = Path(args.output_dir or Path("output") / f"microchop_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    run_dir.mkdir(parents=True, exist_ok=True)

    sample_path = Path(args.sample)
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample not found: {sample_path}")

    midi_path = copy_midi_into(Path(args.midi), run_dir)
    chops = make_chops(args, run_dir)
    midi_events, midi_info = extract_midi_events(midi_path, args.target_track, args.bar_start, args.bar_count)
    render_path, event_map, render_stats = render_events(args, run_dir, midi_events, chops)
    reference_stats = render_reference_outputs(
        run_dir,
        args,
        midi_events,
        midi_info,
        midi_path,
        int(render_stats["sample_rate"]),
        int(render_stats["channels"]),
    )
    write_reports(run_dir, args, chops, midi_events, midi_info, event_map, render_stats, reference_stats)

    return RenderResult(
        run_dir=str(run_dir),
        midi=str(midi_path),
        render=str(render_path),
        reference_midi=reference_stats["reference_midi"],
        reference_wav=reference_stats["reference_wav"],
        chops=len(chops),
        pitched_chops=sum(1 for c in chops if c.get("pitched")),
        midi_events=len(midi_events),
        peak_dbfs=render_stats["peak_dbfs"],
    )


def main() -> None:
    result = render_job(config_from_args(parse_args()))
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
