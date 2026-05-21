#pragma once

#include "BackgroundAnalysisJob.h"
#include "SamplerEngine.h"

class MelodicMicrochopAudioProcessor final
    : public juce::AudioProcessor,
      public AnalysisListener
{
public:
    MelodicMicrochopAudioProcessor();
    ~MelodicMicrochopAudioProcessor() override;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram(int index) override;
    const juce::String getProgramName(int index) override;
    void changeProgramName(int index, const juce::String& newName) override;

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    void loadSampleAsync(const juce::File& file);
    juce::String getStatusText() const;
    int getChopCount() const;
    juce::AudioProcessorValueTreeState& getState();
    void analysisFinished(AnalysisEngine::Result result) override;

private:
    static juce::AudioProcessorValueTreeState::ParameterLayout createParameterLayout();

    juce::AudioProcessorValueTreeState state;
    BackgroundAnalysisJob analysisJob;
    SamplerEngine sampler;
    juce::String status = "Load a sample to begin.";
    juce::File currentSampleFile;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MelodicMicrochopAudioProcessor)
};
