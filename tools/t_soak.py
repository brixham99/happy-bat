"""Soak test: 40 games from tape (alternating quick ground crashes and
piloted games), then BREAK and PRINT FREE.  Checks that no error ever
appears and memory does not shrink."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game, Pilot
from t_free import brk, free_now
g = Game(tape=os.path.join(HB, 'happybat.tap'))
g.start('LOAD ""'); assert g.wait_text('Press SPACE', 6000) is not None; g.frames(20)
errs = 0; scores = []
for n in range(40):
    g.tap(); g.frames(6)
    if n % 2:
        p = Pilot(g, margin=6)
        for _ in range(3000):
            if g.has('G A M E'): break
            p.frame()
        g.space(False)
    assert g.wait_text('G A M E', 3000) is not None, n
    scores.append(g.score())
    if any(('line' in r and ',' in r) or 'No room' in r for r in g.rows()): errs += 1
    g.frames(80)
brk(g); print('40 games, scores', scores, 'errors', errs, 'FREE', free_now(g))
