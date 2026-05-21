#include "ChopManifest.h"

void ChopManifest::clear()
{
    chops.clear();
}

void ChopManifest::addChop(const Chop& chop)
{
    chops.push_back(chop);
}

const std::vector<Chop>& ChopManifest::getChops() const
{
    return chops;
}

juce::var ChopManifest::toVar() const
{
    juce::Array<juce::var> array;
    for (const auto& chop : chops)
    {
        auto* item = new juce::DynamicObject();
        item->setProperty("id", chop.id);
        item->setProperty("startSample", static_cast<double>(chop.startSample));
        item->setProperty("endSample", static_cast<double>(chop.endSample));
        item->setProperty("midiNote", chop.midiNote);
        item->setProperty("confidence", chop.confidence);
        array.add(juce::var(item));
    }
    return juce::var(array);
}

void ChopManifest::fromVar(const juce::var& data)
{
    chops.clear();
    if (! data.isArray())
        return;

    for (const auto& item : *data.getArray())
    {
        if (auto* object = item.getDynamicObject())
        {
            Chop chop;
            chop.id = static_cast<int>(object->getProperty("id"));
            chop.startSample = static_cast<int64_t>(static_cast<double>(object->getProperty("startSample")));
            chop.endSample = static_cast<int64_t>(static_cast<double>(object->getProperty("endSample")));
            chop.midiNote = static_cast<int>(object->getProperty("midiNote"));
            chop.confidence = static_cast<float>(object->getProperty("confidence"));
            chops.push_back(chop);
        }
    }
}
