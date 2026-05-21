#include "MicrochopVoice.h"

void MicrochopVoice::start(const juce::AudioBuffer<float>* sourceAudio, Chop chopToPlay, int midiNote, float velocity)
{
    audio = sourceAudio;
    chop = chopToPlay;
    note = midiNote;
    position = chop.startSample;
    gain = juce::jlimit(0.0f, 1.0f, velocity);
    active = audio != nullptr && chop.endSample > chop.startSample;
}

void MicrochopVoice::stop()
{
    active = false;
}

bool MicrochopVoice::isActive() const
{
    return active;
}

int MicrochopVoice::getMidiNote() const
{
    return note;
}

void MicrochopVoice::render(juce::AudioBuffer<float>& output, int startSample, int numSamples)
{
    if (! active || audio == nullptr)
        return;

    for (int sample = 0; sample < numSamples; ++sample)
    {
        if (position >= chop.endSample || position >= audio->getNumSamples())
        {
            active = false;
            return;
        }

        for (int channel = 0; channel < output.getNumChannels(); ++channel)
        {
            const int sourceChannel = juce::jmin(channel, audio->getNumChannels() - 1);
            output.addSample(channel, startSample + sample, audio->getSample(sourceChannel, static_cast<int>(position)) * gain);
        }
        ++position;
    }
}
