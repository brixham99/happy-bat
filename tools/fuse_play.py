#!/usr/bin/env python3
"""Play Happy Bat in real Fuse and take the screenshots.
Fuse is slowed down (--speed) and a pilot reads the bat and pipes off the
Fuse window (pixels only: yellow bat, green pipes) and taps SPACE through
xdotool, as a player would.  The ROM is the v1.0.1 release ROM; the tape is
loaded with Fuse's tape traps on (instant load) for this session.
Usage: fuse_play.py out_dir [speed]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuse_common import *
import fuse_phase1
OUT = sys.argv[1]; SPEED = int(sys.argv[2]) if len(sys.argv) > 2 else 10
BX, BY = 32, 24                      # display origin inside the Fuse window
YEL, GRN = (255, 254, 0), (0, 254, 0)
def px(im):
    w = im.load()
    return lambda X, Y: w[BX + X, BY + Y]
def bat_y(p):
    for Y in range(16, 168):
        if any(p(X, Y) == YEL for X in range(64, 80)): return Y
    return None
def pipes(p):
    """groups of green columns (skipping the bat's columns) -> (left, right, top, bottom of gap)"""
    cols = {}
    for X in list(range(0, 64)) + list(range(80, 256)):
        g = [Y for Y in range(16, 168) if p(X, Y) == GRN]
        if len(g) > 10:
            # gap = the longest run of non-green rows
            best = (0, 0, 0); run = None
            for Y in range(16, 169):
                if Y < 168 and p(X, Y) != GRN:
                    run = Y if run is None else run
                elif run is not None:
                    if Y - run > best[0]: best = (Y - run, run, Y)
                    run = None
            cols[X] = best[1:]
    groups = []
    for X in sorted(cols):
        if groups and (X - groups[-1][1] <= 1 or (groups[-1][1] == 63 and X == 80)):
            g = groups[-1]; groups[-1] = [g[0], X, max(g[2], cols[X][0]), min(g[3], cols[X][1])]
        else:
            groups.append([X, X, cols[X][0], cols[X][1]])
    return groups

# The --speed option goes in through the wrapper's argument list.
_orig = fuse_phase1.subprocess.Popen
def popen(args, **kw):
    if args and args[0] == 'fuse-sdl': args = args + ['--speed', str(SPEED)]
    return _orig(args, **kw)
fuse_phase1.subprocess.Popen = popen

kill(); f = Fuse(ROM, TAPE, traps=True)
time.sleep(3 * 100 / SPEED)            # let the ROM boot to its prompt
load(f, True, hold=0.12 * 100 / SPEED)
t0 = time.time()
while time.time() - t0 < 300:          # wait for "Press SPACE to start" (row 18)
    time.sleep(1); p = px(grab(f))
    if p(10, 100) == (0, 0, 255) and any(p(X, Y) == YEL for X in range(80, 200) for Y in range(144, 152)): break
print('title after %.0f s' % (time.time() - t0))
time.sleep(4); grab(f).save(os.path.join(OUT, 'fuse_slow_title.png'))
STEP = 2 / 50 * 100 / SPEED          # real seconds per game step (2 frames)
saved = set(); attempt = 0
while attempt < 8 and not {'play', 'score'} <= saved:
    attempt += 1; passes = 0; flaps = 0
    down(); time.sleep(STEP * 1.5); up(); time.sleep(STEP * 2)
    hist = []; held = None; last_flap = 0; prev_next = None
    while True:
        now = time.time(); im = grab(f); p = px(im); y = bat_y(p)
        # game over?  the red box (rows 7-14, columns 24-51 -> x 96..207, y 56..119)
        r = p(150, 60)
        if r[0] > 150 and r[1] < 50 and r[2] < 50: break
        if y is None: time.sleep(0.01); continue
        hist.append((now, y)); hist = hist[-6:]
        v = 0
        if len(hist) >= 3 and hist[-1][0] - hist[0][0] > 0:
            v = (hist[-1][1] - hist[0][1]) / (hist[-1][0] - hist[0][0])   # px per real second
        gs = [g for g in pipes(p) if g[1] >= 60]
        if gs:
            nxt = min(gs); floor = nxt[3] - 8 - 7; ceil = nxt[2]
        else:
            nxt = None; floor = 110; ceil = 30
        if prev_next and (not nxt or nxt[0] > prev_next[0] + 16): passes += 1
        prev_next = nxt
        if held and now - held > STEP * 1.2: up(); held = None
        pred = y + v * STEP * 2.5
        if not held and now - last_flap > STEP * 2.6 and pred > floor and y - 16 > ceil - 4:
            down(); held = now; last_flap = now; flaps += 1
        if passes >= 2 and 'play' not in saved and nxt and 100 < nxt[0] < 180:
            im.save(os.path.join(OUT, 'fuse_play.png')); saved.add('play'); print('play shot, passes', passes)
        if passes >= 6 and 'score' not in saved and nxt and 90 < nxt[0] < 200:
            im.save(os.path.join(OUT, 'fuse_score.png')); saved.add('score'); print('score shot, passes', passes)
        if 'score' in saved and passes >= 7: 
            if held: up(); held = None
            last_flap = now + 1e9      # stop flapping: the bat falls to the ground
        time.sleep(0.005)
    if held: up()
    print('attempt', attempt, 'passes', passes, 'flaps', flaps)
    time.sleep(STEP * 30)
    grab(f).save(os.path.join(OUT, 'fuse_gameover%d.png' % attempt))
    if not {'play', 'score'} <= saved:
        time.sleep(1); down(); time.sleep(STEP * 1.5); up(); time.sleep(STEP * 2)   # SPACE to fly again
f.close(); print('saved', sorted(saved))
