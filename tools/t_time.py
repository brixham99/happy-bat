"""Time the machine code itself (T-states), without the pacing wait."""
import os, sys, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from rig import Spectrum, lib
SYM = {m.group(1): int(m.group(2), 16) for m in (re.match(r'(\S+)\s+EQU\s+0?([0-9A-F]+)H', l) for l in open(os.path.join(HB, 'build/hbcode.sym'))) if m}
s = Spectrum(ROM); s.frame(150)
s.load(60000, open(os.path.join(HB, 'build/hbcode.bin'),'rb').read())
def t(addr):
    s.poke(SYM['lastf'], (s.peek(23672) - 20) & 255)
    a = lib.z_tstates(); s.call(addr); return lib.z_tstates() - a
print('init', t(60000))
worst = 0
for i in range(120):
    if i % 24 == 0: s.poke(60010, 40); s.poke(60011, 88); s.poke(60012, 1)
    s.poke(SYM['y16'], 60 * 4); s.poke(SYM['y16'] + 1, 0)
    worst = max(worst, t(60003))
n = sum(1 for k in range(4) if s.peek(SYM['ptab'] + 4 * k) != 0x80)
print('step, play mode, worst of 120 steps: %d T (%.2f frames); pipes in use now %d' % (worst, worst / 69888, n))
s.poke(60013, 0); print('step, title mode', t(60003))
