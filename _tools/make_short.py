"""Render a SmartPhDs vertical Short (1080x1920 MP4) from a JSON script.

Usage (run from the site root):
  python3 _tools/make_short.py SCRIPT.json OUT.mp4

SCRIPT.json:
{
  "slides": [
    {"kicker": "Small label", "title": "Big text, use \\n for line breaks", "highlight": "words to highlight",
     "body": "Optional smaller text", "before": "optional", "after": "optional", "seconds": 5,
     "say": "Optional voiceover line (defaults to the slide's text)"}
  ],
  "voice": "af_heart", "music": true
}
The last slide is followed by an automatic end card with the logo and smartphds.com.
Each slide is stretched to fit its voiceover. Audio = voiceover (Kokoro, offline) over an
original synthesized music bed, so there is nothing copyrighted in the track.
Needs: Pillow, numpy, ffmpeg, kokoro-onnx + soundfile (pip), fonts in _tools/fonts/.
Voice model files (~350 MB) download once from GitHub into ~/.cache/smartphds-tts.
"""
import json, math, os, subprocess, sys, tempfile, textwrap, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
NAVY, WHITE, MUTED, YELLOW, LIGHT, INK, RED = "#0E1322", "#FFFFFF", "#A9B1C6", "#FFE24D", "#8FA7FF", "#13203B", "#E58A8A"
HERE = os.path.dirname(os.path.abspath(__file__))
BOLD = os.path.join(HERE, "fonts", "FamiljenGrotesk-700.ttf")
MED = os.path.join(HERE, "fonts", "FamiljenGrotesk-500.ttf")
font = lambda path, size: ImageFont.truetype(path, size)

def draw_mark(d, x, y, s, ink=WHITE, acc=LIGHT, width=None):
    """Draw the SmartPhDs hexagon-and-arrow mark at (x, y) with size s (64-unit box)."""
    k = s / 64; w = width or max(3, int(4.5 * k))
    P = lambda a, b: (x + a * k, y + b * k)
    d.line([P(47.3, 24), P(47.3, 44), P(30, 54), P(12.7, 44), P(12.7, 24), P(30, 14)], fill=ink, width=w, joint="curve")
    d.line([P(30, 34), P(56, 8)], fill=acc, width=w)
    d.line([P(47, 8), P(56, 8), P(56, 17)], fill=acc, width=w, joint="curve")
    r = 5.5 * k; cx, cy = P(30, 34); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=YELLOW)

def wrap(text, f, maxw, d):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if d.textlength(t, font=f) <= maxw: cur = t
            else: lines.append(cur); cur = wd
        lines.append(cur)
    return lines

def hexes(d):
    for gx in range(-40, W + 80, 84):
        for gy in range(-40, H + 80, 100):
            pts = [(gx + 21, gy + 3), (gx + 40, gy + 14), (gx + 40, gy + 36), (gx + 21, gy + 47), (gx + 2, gy + 36), (gx + 2, gy + 14), (gx + 21, gy + 3)]
            d.line(pts, fill="#151C2E", width=2)


SR = 24000
TTS_DIR = os.path.expanduser("~/.cache/smartphds-tts")
TTS_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"

def tts_engine():
    from kokoro_onnx import Kokoro
    os.makedirs(TTS_DIR, exist_ok=True)
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        dst = os.path.join(TTS_DIR, f)
        if not os.path.exists(dst):
            print("downloading", f); urllib.request.urlretrieve(TTS_URL + f, dst + ".part"); os.rename(dst + ".part", dst)
    return Kokoro(os.path.join(TTS_DIR, "kokoro-v1.0.onnx"), os.path.join(TTS_DIR, "voices-v1.0.bin"))

def narration(s):
    if s.get("say"): return s["say"]
    parts = [s.get("title", "").replace("\n", " ")]
    if s.get("before"): parts += ["Instead of: " + s["before"], "Try: " + s["after"]]
    if s.get("body"): parts.append(s["body"])
    return " ".join(p.strip() for p in parts if p.strip())

def speak(engine, text, voice):
    samples, sr = engine.create(text, voice=voice, speed=1.05, lang="en-us")
    assert sr == SR
    return np.asarray(samples, dtype=np.float32)

def music_bed(total):
    """Original soft pad + pluck loop (C - Am - F - G), 92 bpm. Generated, so royalty-free."""
    n = int(total * SR); t = np.arange(n) / SR; out = np.zeros(n, np.float32)
    beat = 60 / 92; bar = 4 * beat
    chords = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]
    f = lambda m: 440 * 2 ** ((m - 69) / 12)
    nbars = int(total / bar) + 1
    for b in range(nbars):
        ch = chords[b % 4]; st = int(b * bar * SR); ln = min(int(bar * SR), n - st)
        if ln <= 0: break
        tt = np.arange(ln) / SR
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (bar - tt) / 0.5)
        for m in ch:
            out[st:st + ln] += 0.05 * env * (np.sin(2 * np.pi * f(m) * tt) + 0.3 * np.sin(2 * np.pi * f(m) * 2.003 * tt))
        for k in range(8):  # eighth-note pluck arpeggio, one octave up
            ps = st + int(k * beat / 2 * SR); pl = min(int(0.45 * SR), n - ps)
            if pl <= 0: continue
            pt = np.arange(pl) / SR; m = ch[[1, 2, 3, 2][k % 4]] + 12
            out[ps:ps + pl] += 0.035 * np.exp(-pt * 7) * np.sin(2 * np.pi * f(m) * pt)
    fade = int(1.5 * SR); out[:fade] *= np.linspace(0, 1, fade); out[-fade:] *= np.linspace(1, 0, fade)
    return out


def slide_image(s, idx, total):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    hexes(d)
    # header
    draw_mark(d, 80, 110, 76)
    d.text((176, 128), "Smart", font=font(BOLD, 52), fill=WHITE)
    d.text((176 + d.textlength("Smart", font=font(BOLD, 52)), 128), "PhDs", font=font(BOLD, 52), fill=LIGHT)
    # progress bar
    seg = (W - 160 - (total - 1) * 12) / total
    for i in range(total):
        x0 = 80 + i * (seg + 12)
        d.rounded_rectangle([x0, 230, x0 + seg, 240], radius=5, fill=YELLOW if i <= idx else "#2A3350")
    y = 520
    if s.get("kicker"):
        d.text((80, y), s["kicker"].upper(), font=font(MED, 40), fill=LIGHT); y += 90
    ft = font(BOLD, 104 if len(s.get("title", "")) < 40 else 88)
    hl = s.get("highlight", "")
    for line in wrap(s.get("title", ""), ft, W - 160, d):
        if hl and hl.lower() in line.lower():
            i = line.lower().index(hl.lower())
            pre, mid = line[:i], line[i:i + len(hl)]
            x = 80 + d.textlength(pre, font=ft); wmid = d.textlength(mid, font=ft)
            d.rectangle([x - 8, y + 18, x + wmid + 8, y + ft.size + 14], fill=YELLOW)
            d.text((80, y), pre, font=ft, fill=WHITE); d.text((x, y), mid, font=ft, fill=INK)
            d.text((x + wmid, y), line[i + len(hl):], font=ft, fill=WHITE)
        else:
            d.text((80, y), line, font=ft, fill=WHITE)
        y += int(ft.size * 1.15)
    y += 50
    if s.get("before"):
        for label, txt, col in (("BEFORE", s["before"], RED), ("AFTER", s["after"], YELLOW)):
            d.text((80, y), label, font=font(MED, 34), fill=col); y += 56
            fb = font(MED, 54)
            for line in wrap(txt, fb, W - 160, d):
                d.text((80, y), line, font=fb, fill=WHITE if label == "AFTER" else MUTED); y += 70
            if label == "BEFORE":
                d.line([80, y + 4, W - 120, y + 4], fill="#2A3350", width=2)
            y += 40
    if s.get("body"):
        fb = font(MED, 56)
        for line in wrap(s["body"], fb, W - 160, d):
            d.text((80, y), line, font=fb, fill=MUTED); y += 74
    d.text((80, H - 170), "smartphds.com", font=font(MED, 44), fill=MUTED)
    return im

def end_card():
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im); hexes(d)
    draw_mark(d, W / 2 - 150, 640, 300, width=20)
    fb = font(BOLD, 120); tw = d.textlength("SmartPhDs", font=fb)
    x = (W - tw) / 2
    d.text((x, 1020), "Smart", font=fb, fill=WHITE)
    d.text((x + d.textlength("Smart", font=fb), 1020), "PhDs", font=fb, fill=LIGHT)
    for i, (t, f, c) in enumerate([("Follow for weekly career tips", font(MED, 56), WHITE), ("smartphds.com", font(MED, 52), YELLOW)]):
        w = d.textlength(t, font=f); d.text(((W - w) / 2, 1220 + i * 90), t, font=f, fill=c)
    return im

def main(script, out):
    cfg = json.load(open(script)); slides = cfg["slides"]
    tmp = tempfile.mkdtemp()
    engine = tts_engine(); voice = cfg.get("voice", "af_heart")
    lead = 0.35
    voices = [speak(engine, narration(s), voice) for s in slides]
    voices.append(speak(engine, cfg.get("end_say", "Follow SmartPhDs for weekly career tips. Free resources at smart P H Ds dot com."), voice))
    parts = []
    for i, s in enumerate(slides):
        p = os.path.join(tmp, f"s{i}.png"); slide_image(s, i, len(slides)).save(p)
        parts.append((p, round(max(s.get("seconds", 4), len(voices[i]) / SR + lead + 0.6), 2)))
    p = os.path.join(tmp, "end.png"); end_card().save(p); parts.append((p, round(max(3.5, len(voices[-1]) / SR + lead + 0.8), 2)))
    clips = []
    for i, (img, secs) in enumerate(parts):
        c = os.path.join(tmp, f"c{i}.mp4")
        frames = int(secs * FPS)
        # gentle zoom-in for motion, fade in/out
        vf = (f"scale=1188:2112,zoompan=z='min(1+on/{frames}*0.05,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"fade=t=in:st=0:d=0.35,fade=t=out:st={secs-0.35}:d=0.35,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-t", str(secs), "-vf", vf,
                        "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-an", c], check=True)
        clips.append(c)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    silent = os.path.join(tmp, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    # audio: voice + ducked music bed
    total = sum(sec for _, sec in parts)
    starts, acc = [], 0.0
    for _, sec in parts: starts.append(acc + lead); acc += sec
    bed = music_bed(total) * (0.55 if cfg.get("music", True) else 0)
    duck = np.ones_like(bed); vtrack = np.zeros_like(bed)
    for v, st in zip(voices, starts):
        i = int(st * SR); j = min(i + len(v), len(bed)); vtrack[i:j] += v[:j - i]
        a, b = max(0, i - 2400), min(len(bed), j + 4800); duck[a:b] = 0.45
    k = int(0.15 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mix = vtrack * 0.95 + bed * duck
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.89
    import soundfile as sf
    wav = os.path.join(tmp, "audio.wav"); sf.write(wav, mix, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out, f"{total:.1f}s")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
