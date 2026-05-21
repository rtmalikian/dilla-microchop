#pragma once

#include "AnalysisEngine.h"

class AnalysisListener
{
public:
    virtual ~AnalysisListener() = default;
    virtual void analysisFinished(AnalysisEngine::Result result) = 0;
};

class BackgroundAnalysisJob final : public juce::Thread
{
public:
    explicit BackgroundAnalysisJob(AnalysisListener& listener);
    ~BackgroundAnalysisJob() override;

    void startAnalysis(const juce::File& fileToAnalyse);
    void run() override;

private:
    AnalysisListener& owner;
    juce::File file;
    AnalysisEngine engine;
};
