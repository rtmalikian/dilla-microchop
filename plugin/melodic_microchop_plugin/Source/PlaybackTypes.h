#pragma once

#include <juce_audio_utils/juce_audio_utils.h>

enum class PlaybackMode
{
    oneShot,
    gated,
    loopForward,
    loopForwardReverse,
    loopReverseForward,
    stretch,
    sliceSequence
};

enum class StyleMode
{
    fixed,
    roundRobin,
    randomChop,
    randomPlayback,
    weightedRandom,
    velocityStyle,
    noteRangeStyle,
    alternatingStyle,
    humanizedStyle
};

inline juce::String playbackModeToString(PlaybackMode mode)
{
    switch (mode)
    {
        case PlaybackMode::oneShot: return "one-shot";
        case PlaybackMode::gated: return "gated";
        case PlaybackMode::loopForward: return "loop-forward";
        case PlaybackMode::loopForwardReverse: return "loop-forward-reverse";
        case PlaybackMode::loopReverseForward: return "loop-reverse-forward";
        case PlaybackMode::stretch: return "stretch";
        case PlaybackMode::sliceSequence: return "slice-sequence";
    }
    return "one-shot";
}
