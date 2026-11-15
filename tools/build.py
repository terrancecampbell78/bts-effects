#!/usr/bin/env python3
"""
Builds Backing Track Studio effect plug-ins from the official Airwindows source (MIT).

For every Airwindows effect:
  1. a host build is loaded by tools/probe.cpp (name, controls, defaults; must stay finite on test audio),
  2. effects that pass are built for Android (arm64-v8a, armeabi-v7a) and stripped,
  3. dist/catalog.json lists them with size and SHA-256 per file; dist/catalog.sig signs it (ECDSA P-256).

Usage:
  tools/build.py [--aw-src DIR] [--only Name ...] [--jobs 2] [--key KEY.pem]
Without --aw-src the official repository is cloned into work/airwindows (git, network).
The signing key never goes into this repository.
"""
import argparse, concurrent.futures as cf, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import catalog as cat  # noqa: E402

ABIS = {"arm64-v8a": "aarch64-linux-android29", "armeabi-v7a": "armv7a-linux-androideabi29"}
AW_REPO = "https://github.com/airwindows/airwindows"


def ndk_toolchain(ndk):
    if not ndk:
        base = Path(os.environ.get("ANDROID_HOME", "/opt/android-sdk")) / "ndk"
        ndk = sorted(base.iterdir())[-1]
    tc = Path(ndk) / "toolchains/llvm/prebuilt/linux-x86_64"
    if not (tc / "bin/clang++").exists():
        sys.exit(f"NDK clang not found under {tc}")
    return tc


def run(cmd, **kw):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw)


class Builder:
    def __init__(self, aw, tc, out, work):
        self.aw, self.tc, self.out, self.work = aw, tc, out, work
        self.cxx = str(tc / "bin/clang++")
        # Host build (probe only, never shipped): the NDK's own clang + host libc++, standard ABI namespace.
        cfg = work / "hostcfg"; cfg.mkdir(parents=True, exist_ok=True)
        site = next((tc / "sysroot/usr/include").rglob("__config_site"))
        (cfg / "__config_site").write_text(site.read_text().replace("__ndk1", "__1"))
        self.host = [self.cxx, "--target=x86_64-linux-gnu", "-fuse-ld=lld", "-nostdinc++", "-isystem", str(cfg),
                     "-isystem", str(tc / "sysroot/usr/include/c++/v1"), "-isystem", "/usr/include/x86_64-linux-gnu",
                     "-D_LIBCPP_HAS_THREAD_API_PTHREAD"]
        self.hostlibs = ["-nostartfiles", "-nodefaultlibs", f"-L{tc}/lib", "-l:libc++.a", "-l:libc++abi.a",
                         "-lc", "-lm", "-lpthread", "/lib/x86_64-linux-gnu/libgcc_s.so.1"]
        self.probe = work / "probe"
        r = run(self.host + ["-O2", str(ROOT / "tools/probe.cpp"), "-o", str(self.probe), "-nostartfiles", "-nodefaultlibs",
                             "/usr/lib/x86_64-linux-gnu/crt1.o", "/usr/lib/x86_64-linux-gnu/crti.o"]
                + self.hostlibs[2:] + ["-ldl", "/usr/lib/x86_64-linux-gnu/crtn.o"])
        if r.returncode:
            sys.exit("probe build failed:\n" + r.stderr)

    def src_flags(self, name):
        return ["-O2", "-fPIC", "-shared", "-w", "-fvisibility=hidden", "-ffunction-sections", "-fdata-sections",
                f"-I{ROOT / 'glue'}", f"-I{self.aw / name}", f"-DAW_NAME={name}",
                f'-DAW_SRC1="{name}.cpp"', f'-DAW_SRC2="{name}Proc.cpp"', str(ROOT / "glue/aw_plugin.cpp")]

    def build(self, name):
        hso = self.work / "host" / f"aw.{name}.so"; hso.parent.mkdir(parents=True, exist_ok=True)
        r = run(self.host + self.src_flags(name) + ["-o", str(hso)] + self.hostlibs)
        if r.returncode:
            return name, None, "host build failed: " + r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else "host build failed"
        try:
            p = run([str(self.probe), str(hso)], timeout=60)
        except subprocess.TimeoutExpired:
            return name, None, "probe timed out"
        try:
            info = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:
            return name, None, f"probe crashed (exit {p.returncode})"
        if not info.get("ok"):
            return name, None, f"failed the audio check: {info}"
        files = {}
        for abi, target in ABIS.items():
            so = self.out / abi / f"aw.{name}.so"; so.parent.mkdir(parents=True, exist_ok=True)
            r = run([self.cxx, f"--target={target}"] + self.src_flags(name)
                    + ["-o", str(so), "-Wl,--gc-sections", "-Wl,-z,max-page-size=16384", "-lm"])
            if r.returncode:
                return name, None, f"{abi} build failed"
            run([str(self.tc / "bin/llvm-strip"), "--strip-unneeded", str(so)])
            data = so.read_bytes()
            files[abi] = {"path": f"{abi}/aw.{name}.so", "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        info["files"] = files
        return name, info, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aw-src", help="airwindows plugins/LinuxVST/src (default: clone the official repo)")
    ap.add_argument("--ndk"); ap.add_argument("--only", nargs="*"); ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--out", default=str(ROOT / "dist")); ap.add_argument("--work", default=str(ROOT / "work"))
    ap.add_argument("--key", help="ECDSA P-256 private key (PEM) to sign the catalog")
    a = ap.parse_args()
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    if a.aw_src:
        aw = Path(a.aw_src)
        commit = run(["git", "-C", str(aw), "rev-parse", "HEAD"]).stdout.strip() or "unknown"
    else:
        repo = work / "airwindows"
        if not repo.exists():
            subprocess.check_call(["git", "clone", "--depth", "1", AW_REPO, str(repo)])
        aw = repo / "plugins/LinuxVST/src"
        commit = run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
    out = Path(a.out)
    names = sorted(d.name for d in aw.iterdir() if (d / f"{d.name}.cpp").exists() and (d / f"{d.name}Proc.cpp").exists())
    if a.only:
        names = [n for n in names if n in set(a.only)]
    b = Builder(aw, ndk_toolchain(a.ndk), out, work)
    ok, failed = {}, {}
    t0 = time.time()
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for i, (name, info, err) in enumerate(ex.map(b.build, names), 1):
            if info: ok[name] = info
            else: failed[name] = err
            print(f"[{i}/{len(names)}] {name}: {'ok' if info else err}", flush=True)
    catalog = cat.make(ok, commit)
    (out / "catalog.json").write_text(json.dumps(catalog, indent=1, ensure_ascii=False))
    (work / "failed.json").write_text(json.dumps(failed, indent=1))
    if a.key:
        subprocess.check_call(["openssl", "dgst", "-sha256", "-sign", a.key, "-out", str(out / "catalog.sig"), str(out / "catalog.json")])
    print(f"{len(ok)} effects built, {len(failed)} skipped (see work/failed.json), {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
