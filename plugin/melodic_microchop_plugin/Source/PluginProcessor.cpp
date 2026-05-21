#include "PluginProcessor.h"
#include "PluginEditor.h"

MelodicMicrochopAudioProcessor::MelodicMicrochopAudioProcessor()
    : AudioProcessor(BusesProperties().withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      state(*this, nullptr, "PARAMETERS", createParameterLayout()),
      analysisJob(*this)
{
}

MelodicMicrochopAudioProcessor::~MelodicMicrochopAudioProcessor() = default;

juce::AudioProcessorValueTreeState::ParameterLayout MelodicMicrochopAudioProcessor::createParameterLayout()
{
    std::vector<std::unique_ptr<juce::RangedAudioParameter>> params;
    params.push_back(std::make_unique<juce::AudioParameterChoice>(
        "playbackMode",
        "Playback Mode",
        juce::StringArray { "one-shot", "gated", "loop-forward", "loop-forward-reverse", "loop-reverse-forward", "stretch", "slice-sequence" },
        0));
    params.push_back(std::make_unique<juce::AudioParameterChoice>(
        "styleMode",
        "Style Mode",
        juce::StringArray { "fixed", "round-robin", "random-chop", "random-playback", "weighted-random", "velocity-style", "note-range-style", "alternating-style", "humanized-style" },
        0));
    params.push_back(std::make_unique<juce::AudioParameterFloat>("outputGain", "Output Gain", 0.0f, 1.0f, 0.85f));
    return { params.begin(), params.end() };
}

void MelodicMicrochopAudioProcessor::prepareToPlay(double, int)
{
}

void MelodicMicrochopAudioProcessor::releaseResources()
{
}

bool MelodicMicrochopAudioProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    return layouts.getMainOutputChannelSet() == juce::AudioChannelSet::mono()
        || layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}

void MelodicMicrochopAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
{
    juce::ScopedNoDenormals noDenormals;
    buffer.clear();
    sampler.handleMidi(midiMessages, buffer);
    sampler.renderVoices(buffer);
    buffer.applyGain(*state.getRawParameterValue("outputGain"));
}

juce::AudioProcessorEditor* MelodicMicrochopAudioProcessor::createEditor()
{
    return new MelodicMicrochopAudioProcessorEditor(*this);
}

bool MelodicMicrochopAudioProcessor::hasEditor() const { return true; }
const juce::String MelodicMicrochopAudioProcessor::getName() const { return JucePlugin_Name; }
bool MelodicMicrochopAudioProcessor::acceptsMidi() const { return true; }
bool MelodicMicrochopAudioProcessor::producesMidi() const { return false; }
bool MelodicMicrochopAudioProcessor::isMidiEffect() const { return false; }
double MelodicMicrochopAudioProcessor::getTailLengthSeconds() const { return 0.0; }
int MelodicMicrochopAudioProcessor::getNumPrograms() { return 1; }
int MelodicMicrochopAudioProcessor::getCurrentProgram() { return 0; }
void MelodicMicrochopAudioProcessor::setCurrentProgram(int) {}
const juce::String MelodicMicrochopAudioProcessor::getProgramName(int) { return {}; }
void MelodicMicrochopAudioProcessor::changeProgramName(int, const juce::String&) {}

void MelodicMicrochopAudioProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    auto tree = state.copyState();
    tree.setProperty("samplePath", currentSampleFile.getFullPathName(), nullptr);
    std::unique_ptr<juce::XmlElement> xml(tree.createXml());
    copyXmlToBinary(*xml, destData);
}

void MelodicMicrochopAudioProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    std::unique_ptr<juce::XmlElement> xml(getXmlFromBinary(data, sizeInBytes));
    if (xml != nullptr)
    {
        auto tree = juce::ValueTree::fromXml(*xml);
        if (tree.isValid())
        {
            state.replaceState(tree);
            currentSampleFile = juce::File(tree.getProperty("samplePath").toString());
            if (currentSampleFile.existsAsFile())
                loadSampleAsync(currentSampleFile);
            else if (currentSampleFile.getFullPathName().isNotEmpty())
                status = "Sample missing. Relink it in the plugin.";
        }
    }
}

void MelodicMicrochopAudioProcessor::loadSampleAsync(const juce::File& file)
{
    currentSampleFile = file;
    status = "Analysing " + file.getFileName() + "...";
    analysisJob.startAnalysis(file);
}

juce::String MelodicMicrochopAudioProcessor::getStatusText() const
{
    return status;
}

int MelodicMicrochopAudioProcessor::getChopCount() const
{
    return sampler.getChopCount();
}

juce::AudioProcessorValueTreeState& MelodicMicrochopAudioProcessor::getState()
{
    return state;
}

void MelodicMicrochopAudioProcessor::analysisFinished(AnalysisEngine::Result result)
{
    if (result.error.isNotEmpty())
    {
        status = result.error;
        return;
    }

    sampler.setSource(std::move(result.audio), std::move(result.manifest), result.sampleRate);
    status = "Ready. Chops: " + juce::String(sampler.getChopCount());
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new MelodicMicrochopAudioProcessor();
}
