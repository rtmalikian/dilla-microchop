#pragma once

#include "PlaybackTypes.h"

struct Chop
{
    int id = 0;
    int64_t startSample = 0;
    int64_t endSample = 0;
    int midiNote = -1;
    float confidence = 0.0f;
};

class ChopManifest
{
public:
    void clear();
    void addChop(const Chop& chop);
    const std::vector<Chop>& getChops() const;
    juce::var toVar() const;
    void fromVar(const juce::var& data);

private:
    std::vector<Chop> chops;
};
