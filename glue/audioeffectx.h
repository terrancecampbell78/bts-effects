// Minimal stand-in for the VST2 base class, written for Backing Track Studio so Airwindows effects
// (MIT) build without Steinberg's SDK. Only what the effects use; no plugin hosting.
#pragma once
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <cmath>
typedef int32_t VstInt32;
typedef intptr_t VstIntPtr;
typedef VstIntPtr (*audioMasterCallback)(void*, VstInt32, VstInt32, VstIntPtr, void*, float);
enum VstPlugCategory { kPlugCategUnknown = 0, kPlugCategEffect, kPlugCategSynth, kPlugCategAnalysis, kPlugCategMastering,
    kPlugCategSpacializer, kPlugCategRoomFx, kPlugSurroundFx, kPlugCategRestoration, kPlugCategOfflineProcess,
    kPlugCategShell, kPlugCategGenerator };
enum { kVstMaxProgNameLen = 24, kVstMaxParamStrLen = 8, kVstMaxVendorStrLen = 64, kVstMaxProductStrLen = 64,
    kVstMaxEffectNameLen = 32 };
inline void vst_strncpy(char* d, const char* s, size_t n) { std::strncpy(d, s, n); d[n] = 0; }
inline void float2string(float v, char* t, size_t n) { std::snprintf(t, n + 1, "%.2f", v); }
inline void int2string(VstInt32 v, char* t, size_t n) { std::snprintf(t, n + 1, "%d", (int)v); }
inline void dB2string(float v, char* t, size_t n) { if (v <= 0) vst_strncpy(t, "-oo", n); else float2string(20.f * std::log10(v), t, n); }
class AudioEffect {
public:
    AudioEffect(audioMasterCallback, VstInt32, VstInt32) {}
    virtual ~AudioEffect() {}
    double sampleRate = 48000.0;
    VstInt32 curProgram = 0;
    void setSampleRate(double r) { sampleRate = r; }
    double getSampleRate() { return sampleRate; }
    void setNumInputs(VstInt32) {} void setNumOutputs(VstInt32) {} void setUniqueID(VstInt32) {}
    void canProcessReplacing(bool = true) {} void canDoubleReplacing(bool = true) {} void programsAreChunks(bool = true) {}
    virtual float getParameter(VstInt32) { return 0; }
    virtual void setParameter(VstInt32, float) {}
};
class AudioEffectX : public AudioEffect {
public:
    AudioEffectX(audioMasterCallback a, VstInt32 p, VstInt32 n) : AudioEffect(a, p, n) {}
    virtual VstInt32 canDo(char*) { return 0; }
};
