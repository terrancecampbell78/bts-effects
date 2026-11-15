// Backing Track Studio effect plug-in interface (MIT). A plug-in is one shared library that exports
// bts_plugin(), returning a static description of one effect. The app loads it with dlopen() after checking
// the file's SHA-256 against the signed catalog. Keep this file identical in the app and in bts-effects.
#pragma once
#ifdef __cplusplus
extern "C" {
#endif

#define BTS_PLUGIN_ABI 1
#define BTS_PLUGIN_MAX_PARAMS 16

typedef struct BtsPlugin {
    int abi;                 /* BTS_PLUGIN_ABI */
    const char* name;        /* "Lead Amp" (display name) */
    int numParams;           /* 0..BTS_PLUGIN_MAX_PARAMS */
    const char* paramNames;  /* numParams names, each ending with '\n' */
    void* (*create)(float sampleRate);
    void (*destroy)(void* fx);
    float (*getParam)(void* fx, int i);            /* 0..1 */
    void (*setParam)(void* fx, int i, float v);    /* 0..1; called from the audio thread, must not block */
    /* Stereo, non-interleaved, in -> out (they may not alias); frames <= 4096. Audio thread: no locks/allocation. */
    void (*process)(void* fx, float* inL, float* inR, float* outL, float* outR, int frames);
} BtsPlugin;

const BtsPlugin* bts_plugin(void);

#ifdef __cplusplus
}
#endif
