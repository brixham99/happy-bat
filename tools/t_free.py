import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game
def brk(g):
    g.s.key('^'); g.s.key(' '); g.frames(20); g.s.key(' ', False); g.s.key('^', False); g.frames(20)
def free_now(g):
    g.b.line('CLS'); g.b.line('PRINT FREE')
    return [r.strip() for r in g.rows() if r.strip().isdigit()][-1]
def games(g, n):
    for i in range(n):
        g.tap(); g.frames(20); g.wait_text('G A M E', 3000); g.frames(80)
if __name__ == "__main__":
  for src in ('typed', 'tape'):
      for n in (1, 3):
          g = Game(tape=os.path.join(HB, 'happybat.tap') if src == 'tape' else None)
          g.start('LOAD ""' if src == 'tape' else 'RUN'); g.wait_text('Press SPACE', 6000); g.frames(20)
          games(g, n); brk(g); print(src, n, 'games: FREE', free_now(g))
