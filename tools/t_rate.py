import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game, Pilot
TICK = 0xEA7D
g = Game(); g.start(); g.frames(150); g.tap(); g.frames(10)
p = Pilot(g)
for f in range(30): p.frame()
k0 = g.peek(TICK); seen = []
for f in range(200):
    p.frame(); seen.append(g.peek(TICK))
print('steps in 200 frames:', (seen[-1] - k0) % 256, '-> %.1f steps/s' % (((seen[-1] - k0) % 256) / 4))
d = [ (seen[i] - seen[i-1]) % 256 for i in range(1, len(seen))]
print(''.join(str(x) for x in d[:120]))
