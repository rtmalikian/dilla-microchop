#include "PluginEditor.h"

MelodicMicrochopAudioProcessorEditor::MelodicMicrochopAudioProcessorEditor(MelodicMicrochopAudioProcessor& owner)
    : AudioProcessorEditor(&owner), audioProcessor(owner)
{
    setSize(560, 360);

    title.setText("Melodic Microchop", juce::dontSendNotification);
    title.setFont(juce::FontOptions(24.0f, juce::Font::bold));
    addAndMakeVisible(title);

    addAndMakeVisible(loadButton);
    loadButton.onClick = [this] { chooseSample(); };

    playbackMode.addItemList({ "one-shot", "gated", "loop-forward", "loop-forward-reverse", "loop-reverse-forward", "stretch", "slice-sequence" }, 1);
    styleMode.addItemList({ "fixed", "round-robin", "random-chop", "random-playback", "weighted-random", "velocity-style", "note-range-style", "alternating-style", "humanized-style" }, 1);
    addAndMakeVisible(playbackMode);
    addAndMakeVisible(styleMode);

    outputGain.setSliderStyle(juce::Slider::LinearHorizontal);
    outputGain.setTextBoxStyle(juce::Slider::TextBoxRight, false, 72, 24);
    addAndMakeVisible(outputGain);

    addAndMakeVisible(status);
    status.setText(audioProcessor.getStatusText(), juce::dontSendNotification);

    playbackAttachment = std::make_unique<ComboAttachment>(audioProcessor.getState(), "playbackMode", playbackMode);
    styleAttachment = std::make_unique<ComboAttachment>(audioProcessor.getState(), "styleMode", styleMode);
    gainAttachment = std::make_unique<SliderAttachment>(audioProcessor.getState(), "outputGain", outputGain);

    startTimerHz(10);
}

MelodicMicrochopAudioProcessorEditor::~MelodicMicrochopAudioProcessorEditor() = default;

void MelodicMicrochopAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff171717));
    g.setColour(juce::Colour(0xfff2f2f2));
}

void MelodicMicrochopAudioProcessorEditor::resized()
{
    auto area = getLocalBounds().reduced(24);
    title.setBounds(area.removeFromTop(36));
    loadButton.setBounds(area.removeFromTop(34).removeFromLeft(160));
    area.removeFromTop(18);
    playbackMode.setBounds(area.removeFromTop(34));
    area.removeFromTop(10);
    styleMode.setBounds(area.removeFromTop(34));
    area.removeFromTop(10);
    outputGain.setBounds(area.removeFromTop(34));
    area.removeFromTop(18);
    status.setBounds(area.removeFromTop(80));
}

void MelodicMicrochopAudioProcessorEditor::timerCallback()
{
    status.setText(audioProcessor.getStatusText(), juce::dontSendNotification);
}

void MelodicMicrochopAudioProcessorEditor::chooseSample()
{
    auto chooser = std::make_shared<juce::FileChooser>(
        "Choose a sample",
        juce::File(),
        "*.wav;*.aif;*.aiff");

    chooser->launchAsync(juce::FileBrowserComponent::openMode | juce::FileBrowserComponent::canSelectFiles,
        [this, chooser](const juce::FileChooser& fc) {
            const auto file = fc.getResult();
            if (file.existsAsFile())
                audioProcessor.loadSampleAsync(file);
        });
}
