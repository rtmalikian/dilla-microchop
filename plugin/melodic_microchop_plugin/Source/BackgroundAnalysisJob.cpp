#include "BackgroundAnalysisJob.h"

BackgroundAnalysisJob::BackgroundAnalysisJob(AnalysisListener& listener)
    : juce::Thread("Melodic Microchop Analysis"), owner(listener)
{
}

BackgroundAnalysisJob::~BackgroundAnalysisJob()
{
    stopThread(4000);
}

void BackgroundAnalysisJob::startAnalysis(const juce::File& fileToAnalyse)
{
    stopThread(4000);
    file = fileToAnalyse;
    startThread();
}

void BackgroundAnalysisJob::run()
{
    auto result = engine.analyseFile(file);
    juce::MessageManager::callAsync([this, completedResult = std::move(result)]() mutable {
        owner.analysisFinished(std::move(completedResult));
    });
}
