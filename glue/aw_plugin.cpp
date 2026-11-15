// Glue (MIT): turns one Airwindows effect into a Backing Track Studio plug-in. Compiled once per effect with
//   -DAW_NAME=<Name> -DAW_SRC1='"<Name>.cpp"' -DAW_SRC2='"<Name>Proc.cpp"' -I<airwindows src>/<Name>
// It includes that effect's own two source files, unmodified.
#include "bts_plugin.h"
#define createEffectInstance bts_aw_unused_create
#define BTS_STR2(x) #x
#define BTS_STR(x) BTS_STR2(x)
#include AW_SRC1
#include AW_SRC2
#undef createEffectInstance
#include <string>

namespace {
struct Inst { AW_NAME* e; };

std::string g_names;
char g_title[80];
int g_n = 0;

void* create(float sr) {
    auto* e = new AW_NAME(nullptr);
    e->setSampleRate(sr);
    return new Inst{e};
}
void destroy(void* p) { auto* i = static_cast<Inst*>(p); delete i->e; delete i; }
float getParam(void* p, int k) { return (k >= 0 && k < g_n) ? static_cast<Inst*>(p)->e->getParameter(k) : 0.f; }
void setParam(void* p, int k, float v) { if (k >= 0 && k < g_n) static_cast<Inst*>(p)->e->setParameter(k, v); }
void process(void* p, float* inL, float* inR, float* outL, float* outR, int frames) {
    float* in[2] = {inL, inR};
    float* out[2] = {outL, outR};
    static_cast<Inst*>(p)->e->processReplacing(in, out, frames);
}

BtsPlugin g_plugin;
bool g_ready = false;
} // namespace

extern "C" __attribute__((visibility("default"))) const BtsPlugin* bts_plugin(void) {
    if (!g_ready) {
        AW_NAME probe(nullptr);
        g_n = kNumParameters < BTS_PLUGIN_MAX_PARAMS ? kNumParameters : BTS_PLUGIN_MAX_PARAMS;
        char buf[256];
        for (int k = 0; k < g_n; k++) { buf[0] = 0; probe.getParameterName(k, buf); g_names += buf; g_names += '\n'; }
        g_title[0] = 0; probe.getEffectName(g_title);
        if (!g_title[0]) std::snprintf(g_title, sizeof g_title, "%s", BTS_STR(AW_NAME));
        g_plugin = BtsPlugin{BTS_PLUGIN_ABI, g_title, g_n, g_names.c_str(), create, destroy, getParam, setParam, process};
        g_ready = true;
    }
    return &g_plugin;
}
