#!/usr/bin/env python3
"""Static smoke checks for the JUCE plugin scaffold."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin" / "melodic_microchop_plugin"


def require(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Missing {path.relative_to(ROOT)}")
    return path.read_text()


def main() -> None:
    cmake = require(PLUGIN / "CMakeLists.txt")
    processor = require(PLUGIN / "Source" / "PluginProcessor.cpp")
    analysis = require(PLUGIN / "Source" / "BackgroundAnalysisJob.cpp")
    sampler = require(PLUGIN / "Source" / "SamplerEngine.cpp")

    required_cmake = [
        "GIT_TAG 8.0.12",
        "FORMATS VST3 AU Standalone",
        "NEEDS_MIDI_INPUT TRUE",
        "juce_audio_utils",
    ]
    for item in required_cmake:
        if item not in cmake:
            raise AssertionError(f"CMake missing {item}")

    required_processor = [
        "processBlock",
        "sampler.handleMidi",
        "sampler.renderVoices",
        "loadSampleAsync",
        "analysisFinished",
    ]
    for item in required_processor:
        if item not in processor:
            raise AssertionError(f"Processor missing {item}")

    if "startThread()" not in analysis or "MessageManager::callAsync" not in analysis:
        raise AssertionError("Background analysis is not clearly async")

    if "message.isNoteOn()" not in sampler or "message.isNoteOff()" not in sampler:
        raise AssertionError("Sampler does not handle MIDI note on/off")

    print("plugin smoke checks passed")


if __name__ == "__main__":
    main()
