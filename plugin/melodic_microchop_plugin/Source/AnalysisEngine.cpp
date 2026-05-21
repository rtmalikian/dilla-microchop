#include "AnalysisEngine.h"

AnalysisEngine::Result AnalysisEngine::analyseFile(const juce::File& audioFile) const
{
    Result result;
    juce::AudioFormatManager formats;
    formats.registerBasicFormats();

    std::unique_ptr<juce::AudioFormatReader> reader(formats.createReaderFor(audioFile));
    if (reader == nullptr)
    {
        result.error = "Unsupported or unreadable audio file.";
        return result;
    }

    result.sampleRate = reader->sampleRate;
    result.audio.setSize(static_cast<int>(reader->numChannels), static_cast<int>(reader->lengthInSamples));
    reader->read(&result.audio, 0, static_cast<int>(reader->lengthInSamples), 0, true, true);

    const int minChop = static_cast<int>(0.045 * result.sampleRate);
    const int maxChop = static_cast<int>(0.260 * result.sampleRate);
    const int total = result.audio.getNumSamples();
    int id = 0;

    for (int start = 0; start + minChop < total; start += maxChop)
    {
        const int end = juce::jmin(total, start + maxChop);
        Chop chop;
        chop.id = id++;
        chop.startSample = start;
        chop.endSample = end;
        chop.midiNote = estimateMidiNoteFromZeroCrossing(result.audio, start, end, result.sampleRate);
        chop.confidence = chop.midiNote >= 0 ? 0.35f : 0.0f;
        result.manifest.addChop(chop);
    }

    return result;
}

int AnalysisEngine::estimateMidiNoteFromZeroCrossing(const juce::AudioBuffer<float>& audio, int start, int end, double sampleRate)
{
    if (audio.getNumSamples() == 0 || end <= start)
        return -1;

    const auto* channel = audio.getReadPointer(0);
    int crossings = 0;
    float previous = channel[start];

    for (int i = start + 1; i < end; ++i)
    {
        const float current = channel[i];
        if ((previous <= 0.0f && current > 0.0f) || (previous >= 0.0f && current < 0.0f))
            ++crossings;
        previous = current;
    }

    const double seconds = static_cast<double>(end - start) / sampleRate;
    if (seconds <= 0.0 || crossings < 2)
        return -1;

    const double frequency = (static_cast<double>(crossings) * 0.5) / seconds;
    if (frequency < 30.0 || frequency > 5000.0)
        return -1;

    return static_cast<int>(std::round(69.0 + 12.0 * std::log2(frequency / 440.0)));
}
