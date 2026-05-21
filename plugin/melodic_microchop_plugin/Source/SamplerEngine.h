#pragma once

#include "MicrochopVoice.h"

class SamplerEngine
{
public:
    void setSource(juce::AudioBuffer<float> newAudio, ChopManifest newManifest, double newSampleRate);
    void handleMidi(const juce::MidiBuffer& midi, juce::AudioBuffer<float>& output);
    void renderVoices(juce::AudioBuffer<float>& output);
    bool hasSource() const;
    int getChopCount() const;

private:
    const Chop* chooseChopForNote(int midiNote);

    juce::AudioBuffer<float> audio;
    ChopManifest manifest;
    double sampleRate = 44100.0;
    std::array<MicrochopVoice, 32> voices;
    size_t roundRobin = 0;
};
