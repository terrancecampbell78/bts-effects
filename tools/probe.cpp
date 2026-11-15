// Host-side check (MIT) of one built plug-in: prints JSON with its name, controls, defaults and whether it
// stays finite and sane on test audio at default, all-min and all-max settings, plus its speed.
// Usage: probe <plugin.so>
#include "../glue/bts_plugin.h"
#include <dlfcn.h>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

static std::string esc(const std::string& s) {
    std::string o; for (char c : s) { if (c == '"' || c == '\\') o += '\\'; if ((unsigned char)c >= 32) o += c; } return o;
}

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    void* h = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!h) { std::printf("{\"ok\":false,\"error\":\"%s\"}\n", esc(dlerror()).c_str()); return 1; }
    auto fn = (const BtsPlugin* (*)()) dlsym(h, "bts_plugin");
    const BtsPlugin* p = fn ? fn() : nullptr;
    if (!p || p->abi != BTS_PLUGIN_ABI) { std::printf("{\"ok\":false,\"error\":\"no bts_plugin\"}\n"); return 1; }
    const float sr = 48000.f; const int N = 256;
    void* fx = p->create(sr);
    std::vector<float> defs; for (int i = 0; i < p->numParams; i++) defs.push_back(p->getParam(fx, i));
    std::vector<float> inL(N), inR(N), outL(N), outR(N);
    unsigned seed = 1; double phase = 0;
    float peak[3] = {0, 0, 0}; bool finite = true; double secs = 0;
    for (int pass = 0; pass < 3; pass++) {
        if (pass > 0) for (int i = 0; i < p->numParams; i++) p->setParam(fx, i, pass == 1 ? 0.f : 1.f);
        auto t0 = std::chrono::steady_clock::now();
        for (int b = 0; b < (int)(sr * 2) / N; b++) {          // 2 s per pass: guitar-ish sine + a little noise
            for (int i = 0; i < N; i++) {
                seed = seed * 1664525u + 1013904223u;
                float n = ((seed >> 9) / 8388608.f - 1.f) * 0.05f;
                float s = 0.4f * (float)std::sin(phase) + n; phase += 2 * M_PI * 196.0 / sr;
                inL[i] = s; inR[i] = s * 0.9f;
            }
            p->process(fx, inL.data(), inR.data(), outL.data(), outR.data(), N);
            for (int i = 0; i < N; i++) {
                float a = std::fabs(outL[i]), c = std::fabs(outR[i]);
                if (!std::isfinite(a) || !std::isfinite(c)) finite = false;
                else { if (a > peak[pass]) peak[pass] = a; if (c > peak[pass]) peak[pass] = c; }
            }
        }
        secs += std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    }
    p->destroy(fx);
    std::string names = p->paramNames ? p->paramNames : "";
    std::printf("{\"ok\":%s,\"name\":\"%s\",\"params\":[", (finite && peak[0] < 8.f) ? "true" : "false", esc(p->name).c_str());
    size_t a = 0; int k = 0;
    while (k < p->numParams) { size_t e = names.find('\n', a); if (e == std::string::npos) e = names.size();
        std::printf("%s\"%s\"", k ? "," : "", esc(names.substr(a, e - a)).c_str()); a = e + 1; k++; }
    std::printf("],\"defaults\":[");
    for (size_t i = 0; i < defs.size(); i++) std::printf("%s%.4f", i ? "," : "", defs[i]);
    std::printf("],\"peak\":[%.3f,%.3f,%.3f],\"finite\":%s,\"rt\":%.1f}\n", peak[0], peak[1], peak[2], finite ? "true" : "false", 6.0 / secs);
    return 0;
}
