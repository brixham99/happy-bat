import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game
g = Game(); g.start(); g.frames(200)
for r in g.rows(): 
    if r: print('|' + r)
g.shot('/tmp/hb_title1.png')
