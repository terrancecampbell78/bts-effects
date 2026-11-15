"""Catalog for Backing Track Studio's Effect manager: display name, category and a short description per effect."""
import re, time

# Category rules, first match wins (on the Airwindows name). Order matters: "TapeDelay" is Delay, not Tape.
RULES = [
    ("Dither", r"Dither|TPDF|NotJustAnother|DitherMe|Ditherbox|uLaw"),
    ("Console", r"^Console|Channel\d*$|Buss$|^PurestConsole|^C5Raw|^CStrip|^Desk|TransDesk|TubeDesk|^EveryConsole|^PD(Buss|Channel)|^ConsoleX|X2Buss|ShortBuss|BussColors"),
    ("Amps & cabs", r"Amp$|^Cabs|^Cans|^Mackity|GuitarConditioner|WoodenBox|WoodenChest|^BassKit|Pointy|Punchy|Chimey"),
    ("Delay", r"Delay|Echo|^Doublelay|PitchDelay|SampleDelay|TapeDelay"),
    ("Reverb", r"Verb|^Galactic|^kCathedral|^kPlate|^kChamber|^kGuitarHall|^kCosmos|^kBeyond|^kCyberCity|^kRockstar|^kStation|^kWoodRoom|^kAlien|Chamber|Ambience|^Reverb|Infinity|MatrixVerb|NonlinearSpace|Dattorro|^Cathedral|^Room|Hall"),
    ("Modulation", r"Chorus|Ensemble|Tremolo|TremoSquare|Vibrato|AutoPan|Flutter|^Pan|RingMod|GalacticVibe|Doubler|StereoFX|Wider|Spread|Weave|Swell"),
    ("Tape & vinyl", r"Tape|Oxide|Vinyl|IronOxide|FromTape|ToTape|Discontapeity|GrooveWear|ChromeOxide"),
    ("Dynamics", r"Comp|Pressure|Gate|Gatelope|Limit|Clip|VariMu|Dyno|Dynamics|Slam|Squish|Pop\d*$|Thunder|Surge|Logical|Pyewacket|BrassRider|Recurve|DeEss|DeBess|Sidepass|Mastering|Loud|Energy|PeaksOnly"),
    ("EQ & filter", r"EQ|pass|Pass|Lowpass|Highpass|Notch|Biquad|Baxandall|^Air|^Bass(Drive)?$|Treble|Filter|Isolator|ToneSlant|Hull|Holt|Kalman|^XRegion|^ZRegion|^YNot|^Z(Low|High|Band)|^Y(Low|High|Band)|^X(Low|High|Band)|SmoothEQ|Elliptical|Average|Precious|Capacitor|Silhouette|ResEQ|Focus|Sweeten|Darkness|^Dark$|SubTight|SubsOnly|Infrasonic|Ultrasonic|UltrasonX|Hypersonic|HypersonX|DubSub|Weight|Slew|Acceleration|Coils|Wolfbot|ElectroHat"),
    ("Drive & saturation", r"Drive|Distortion|Density|Tube|Saturation|Fire|Grind|Crunch|Mojo|Dirt|Edge|Spiral|Righteous|Creature|Cojones|Drive|Hard|Fracture|Inflamer|Pafnuty|Huge|Bite|Cider|Coat|Desk|Interstage|Nikola|Melt|Golem|Shape|Wave|Trianglizer|SingleEndedTriode|PowerSag|Preponderant|Exciter|Smooth|Elation|Hype|Highimpact|HighImpact|Monitoring|Mojo|Point|Texturize|Sinew|Apicolypse|Facet|Calibre|Gringer|Dubly|Silken|Srsly|TakeCare"),
    ("Lo-fi & glitch", r"DeRez|Bit|Crush|Glitch|Decimat|Deckwrecka|DeCrackle|Disintegrate|DustBunny|Noise|Hiss|PitchNasty|VoiceOfTheStarship|GlitchShifter|DeNoise"),
    ("Pitch", r"Pitch|Shifter"),
    ("Utility", r"Mono|Side|MidSide|Gain|Trim|Flip|Balanced|Remap|Peaks|Calibre|DCVoltage|Fader|EdIsDim|Cans|Monitoring|Phase|Polarity|Sample|Point|Fade|Purest|BitShift|LeftoMono|RightoMono|MoNoam|Zoom|Pear|Pockey|Podcast|Voice|AQuick|Pear"),
]

ABOUT = {
    "Amps & cabs": "Guitar or bass amp and speaker-cabinet sound.",
    "Drive & saturation": "Adds warmth, grit or distortion.",
    "Delay": "Echoes and repeats.",
    "Reverb": "Room, hall or plate space.",
    "Modulation": "Movement: chorus, tremolo, vibrato, stereo width.",
    "Tape & vinyl": "Tape or record character: saturation, wobble, wear.",
    "Dynamics": "Controls loudness: compression, limiting, gating, clipping.",
    "EQ & filter": "Shapes tone: EQ, low/high-pass and other filters.",
    "Lo-fi & glitch": "Bit reduction, noise and glitch effects.",
    "Pitch": "Pitch shifting and pitch effects.",
    "Console": "Mixing-console emulation (meant for every track plus the mix bus).",
    "Dither": "Mastering tool for reducing bit depth; not useful on single tracks.",
    "Utility": "Tools: mono, stereo, gain and phase.",
    "Other": "Airwindows effect.",
}

# A few hand-written descriptions for well-known ones (the rest get the category text).
KNOWN = {
    "LeadAmp": "High-gain lead guitar amp.", "BigAmp": "Big, full guitar amp.", "MidAmp": "Mid-gain guitar amp.",
    "LilAmp": "Small practice-amp crunch.", "FireAmp": "Hot, bright lead amp.", "GrindAmp": "Heavy, grinding high-gain amp.",
    "BassAmp": "Bass amp with sub and drive.", "Cabs": "Guitar speaker cabinets (choose type and miking).",
    "TapeDelay2": "Warm tape echo.", "PitchDelay": "Delay that shifts pitch on the repeats.", "Tremolo": "Classic volume tremolo.",
    "Vibrato": "Pitch vibrato.", "StereoChorus": "Stereo chorus.", "AutoPan": "Moves the sound left and right.",
    "VariMu": "Smooth tube-style bus compressor.", "SoftGate": "Gentle noise gate.", "kCathedral3": "Huge cathedral reverb.",
    "kGuitarHall2": "Reverb designed for guitar.", "Verbity2": "Rich, smooth reverb.", "ToVinyl4": "Vinyl record sound.",
    "Baxandall2": "Simple bass and treble tone controls.", "DeEss": "Tames harsh 's' sounds.", "RingModulator": "Metallic, bell-like ring modulation.",
}


def category(name):
    for cat, rx in RULES:
        if re.search(rx, name):
            return cat
    return "Other"


def display(name):
    n = name[1:] if re.match(r"^k[A-Z]", name) else name          # Airwindows "k" reverbs: kCathedral3 -> Cathedral 3
    n = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)", " ", n)
    return n


def make(built, commit):
    effects = []
    for name, info in sorted(built.items(), key=lambda kv: display(kv[0]).lower()):
        c = category(name)
        effects.append({
            "id": f"aw.{name}", "name": display(name), "library": "Airwindows", "category": c,
            "about": KNOWN.get(name, ABOUT[c]), "params": info["params"], "defaults": info["defaults"],
            "speed": info.get("rt"), "files": info["files"],
        })
    return {
        "format": 1, "abi": 1, "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": {"name": "Airwindows by Chris Johnson", "url": "https://github.com/airwindows/airwindows",
                   "commit": commit, "license": "MIT"},
        "effects": effects,
    }
