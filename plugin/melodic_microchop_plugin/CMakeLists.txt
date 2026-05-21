cmake_minimum_required(VERSION 3.22)

project(MelodicMicrochopPlugin VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_OSX_DEPLOYMENT_TARGET "11.0" CACHE STRING "Minimum macOS deployment target")

include(FetchContent)

FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.12
)

FetchContent_MakeAvailable(JUCE)

juce_add_plugin(MelodicMicrochop
    COMPANY_NAME "Raphael Malikian"
    BUNDLE_ID "com.raphaelmalikian.melodicmicrochop.plugin"
    PLUGIN_MANUFACTURER_CODE RMal
    PLUGIN_CODE Dmcp
    FORMATS VST3 AU Standalone
    PRODUCT_NAME "Melodic Microchop"
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS TRUE
    COPY_PLUGIN_AFTER_BUILD FALSE
)

target_sources(MelodicMicrochop
    PRIVATE
        Source/AnalysisEngine.cpp
        Source/BackgroundAnalysisJob.cpp
        Source/ChopManifest.cpp
        Source/MicrochopVoice.cpp
        Source/PluginEditor.cpp
        Source/PluginProcessor.cpp
        Source/SamplerEngine.cpp
)

target_include_directories(MelodicMicrochop
    PRIVATE
        Source
)

target_compile_definitions(MelodicMicrochop
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(MelodicMicrochop
    PRIVATE
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)
