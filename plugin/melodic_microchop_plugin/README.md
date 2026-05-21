# Melodic Microchop JUCE Plugin

This is the native DAW plugin scaffold for Melodic Microchop.

The plugin target is macOS **VST3 + AU** with a standalone build for debugging.
It is intentionally separate from the Python desktop app. The DAW plugin should
perform full chopping inside the DAW, but analysis must run on a background
thread and never in the audio callback.

## Build

```bash
cmake -S plugin/melodic_microchop_plugin -B plugin/melodic_microchop_plugin/build -DCMAKE_BUILD_TYPE=Release
cmake --build plugin/melodic_microchop_plugin/build --config Release
```

JUCE `8.0.12` is fetched by CMake during configure.

## Manual Install

After a successful build, copy the generated bundles:

```bash
mkdir -p ~/Library/Audio/Plug-Ins/VST3
mkdir -p ~/Library/Audio/Plug-Ins/Components
cp -R plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/VST3/Melodic\\ Microchop.vst3 ~/Library/Audio/Plug-Ins/VST3/
cp -R plugin/melodic_microchop_plugin/build/MelodicMicrochop_artefacts/Release/AU/Melodic\\ Microchop.component ~/Library/Audio/Plug-Ins/Components/
```

Validate the AU:

```bash
auval -v aumu Dmcp RMal
```

## Current Scaffold

- `PluginProcessor`: audio/MIDI entry point and parameter state.
- `PluginEditor`: sample loading UI and analysis status.
- `BackgroundAnalysisJob`: async file analysis.
- `AnalysisEngine`: placeholder C++ chopping/pitch analysis.
- `SamplerEngine`: MIDI note handling and voice mixing.
- `MicrochopVoice`: sample playback voice.
- `ChopManifest`: serializable analysis data.

The first scaffold can load an audio sample, run a lightweight placeholder
analysis job, and trigger one-shot sample playback from MIDI. The Python
analysis quality is not fully ported yet.
