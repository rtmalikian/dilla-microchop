#pragma once

#include "ChopManifest.h"

class AnalysisEngine
{
public:
    struct Result
    {
        juce::AudioBuffer<float> audio;
        double sampleRate = 44100.0;
        ChopManifest manifest;
        juce::String error;
    };

    Result analyseFile(const juce::File& audioFile) const;

private:
    static int estimateMidiNoteFromZeroCrossing(const juce::AudioBuffer<float>& audio, int start, int end, double sampleRate);
};
