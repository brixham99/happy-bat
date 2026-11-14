import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game, Pilot
g = Game(); g.start(); g.frames(150); g.tap(); g.frames(10)
p = Pilot(g, margin=int(sys.argv[1]) if len(sys.argv) > 1 else 6)
for f in range(1, 30001):
    p.frame()
    if f % 1000 == 0:
        print(f, g.rows()[0].strip(), '| y', g.y())
        if g.has('G A M E'): break
g.shot('/tmp/hb_play4.png')
