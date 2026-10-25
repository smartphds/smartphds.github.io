"""Render a SmartPhDs vertical Short (1080x1920 MP4) from a JSON script.

Usage (run from the site root):
  python3 _tools/make_short.py SCRIPT.json OUT.mp4

SCRIPT.json:
{
  "slides": [
    {"kicker": "Small label", "title": "Big text, use \\n for line breaks", "highlight": "words to highlight",
     "body": "Optional smaller text", "before": "optional", "after": "optional", "seconds": 5}
  ]
}
The last slide is followed by an automatic end card with the logo and smartphds.com.
Needs: Pillow, ffmpeg, fonts in _tools/fonts/.
"""
import json, math, os, subprocess, sys, tempfile, textwrap
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
    slides = json.load(open(script))["slides"]
    tmp = tempfile.mkdtemp()
    parts = []
    for i, s in enumerate(slides):
        p = os.path.join(tmp, f"s{i}.png"); slide_image(s, i, len(slides)).save(p); parts.append((p, s.get("seconds", 5)))
    p = os.path.join(tmp, "end.png"); end_card().save(p); parts.append((p, 3.5))
    clips = []
    for i, (img, secs) in enumerate(parts):
        c = os.path.join(tmp, f"c{i}.mp4")
        frames = int(secs * FPS)
        # gentle zoom-in for motion, fade in/out
        vf = (f"scale=1188:2112,zoompan=z='min(1+on/{frames}*0.05,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"fade=t=in:st=0:d=0.35,fade=t=out:st={secs-0.35}:d=0.35,format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-t", str(secs), "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-c:a", "aac", "-b:a", "96k", "-shortest", c], check=True)
        clips.append(c)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out], check=True)
    print("wrote", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
