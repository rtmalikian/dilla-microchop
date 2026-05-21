#include "SamplerEngine.h"

void SamplerEngine::setSource(juce::AudioBuffer<float> newAudio, ChopManifest newManifest, double newSampleRate)
{
    audio = std::move(newAudio);
    manifest = std::move(newManifest);
    sampleRate = newSampleRate;
    for (auto& voice : voices)
        voice.stop();
}

void SamplerEngine::handleMidi(const juce::MidiBuffer& midi, juce::AudioBuffer<float>&)
{
    for (const auto metadata : midi)
    {
        const auto message = metadata.getMessage();
        if (message.isNoteOn())
        {
            if (const auto* chop = chooseChopForNote(message.getNoteNumber()))
            {
                auto voice = std::find_if(voices.begin(), voices.end(), [](const auto& item) { return ! item.isActive(); });
                if (voice == voices.end())
                    voice = voices.begin();
                voice->start(&audio, *chop, message.getNoteNumber(), message.getFloatVelocity());
            }
        }
        else if (message.isNoteOff())
        {
            for (auto& voice : voices)
                if (voice.getMidiNote() == message.getNoteNumber())
                    voice.stop();
        }
    }
}

void SamplerEngine::renderVoices(juce::AudioBuffer<float>& output)
{
    for (auto& voice : voices)
        voice.render(output, 0, output.getNumSamples());
}

bool SamplerEngine::hasSource() const
{
    return audio.getNumSamples() > 0 && ! manifest.getChops().empty();
}

int SamplerEngine::getChopCount() const
{
    return static_cast<int>(manifest.getChops().size());
}

const Chop* SamplerEngine::chooseChopForNote(int midiNote)
{
    const auto& chops = manifest.getChops();
    if (chops.empty())
        return nullptr;

    auto exact = std::find_if(chops.begin(), chops.end(), [midiNote](const auto& chop) {
        return chop.midiNote == midiNote;
    });
    if (exact != chops.end())
        return &(*exact);

    const auto index = roundRobin++ % chops.size();
    return &chops[index];
}
