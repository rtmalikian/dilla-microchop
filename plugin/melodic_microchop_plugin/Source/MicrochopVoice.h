#pragma once

#include "ChopManifest.h"

class MicrochopVoice
{
public:
    void start(const juce::AudioBuffer<float>* sourceAudio, Chop chopToPlay, int midiNote, float velocity);
    void stop();
    bool isActive() const;
    int getMidiNote() const;
    void render(juce::AudioBuffer<float>& output, int startSample, int numSamples);

private:
    const juce::AudioBuffer<float>* audio = nullptr;
    Chop chop;
    int note = -1;
    int64_t position = 0;
    float gain = 0.0f;
    bool active = false;
};
