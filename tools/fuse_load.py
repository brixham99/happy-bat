#!/usr/bin/env python3
"""Load happybat.tap in real Fuse at full speed with the tape traps OFF
(the ROM reads the real tape signal), check it auto-runs to the title
screen, and save the screenshot.  Usage: fuse_load.py out.png [--traps]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuse_common import *
TRAPS = '--traps' in sys.argv
kill(); f = Fuse(ROM, TAPE, traps=TRAPS); time.sleep(3)
load(f, TRAPS); t0 = time.time()
while time.time() - t0 < 180:
    time.sleep(1); im = grab(f); w = im.load()
    if w[42, 124] == (0, 0, 255) and any(w[32 + X, 24 + Y] == (255, 254, 0) for X in range(80, 200) for Y in range(144, 152)): break
print('title after %.0f s (traps %s)' % (time.time() - t0, 'on' if TRAPS else 'off'))
time.sleep(3); f.shot(sys.argv[1]); f.close()
