#pragma once

#include "PluginProcessor.h"

class MelodicMicrochopAudioProcessorEditor final
    : public juce::AudioProcessorEditor,
      public juce::Timer
{
public:
    explicit MelodicMicrochopAudioProcessorEditor(MelodicMicrochopAudioProcessor&);
    ~MelodicMicrochopAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void timerCallback() override;

private:
    void chooseSample();

    MelodicMicrochopAudioProcessor& audioProcessor;
    juce::TextButton loadButton { "Load Sample" };
    juce::Label title;
    juce::Label status;
    juce::ComboBox playbackMode;
    juce::ComboBox styleMode;
    juce::Slider outputGain;

    using ComboAttachment = juce::AudioProcessorValueTreeState::ComboBoxAttachment;
    using SliderAttachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    std::unique_ptr<ComboAttachment> playbackAttachment;
    std::unique_ptr<ComboAttachment> styleAttachment;
    std::unique_ptr<SliderAttachment> gainAttachment;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(MelodicMicrochopAudioProcessorEditor)
};
