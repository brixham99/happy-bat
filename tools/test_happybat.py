#!/usr/bin/env python3
"""Happy Bat tests in the OpticOS test rig, with the v1.0.1 ROM.
Each test starts from a fresh machine.  Run: python3 tools/test_happybat.py"""
import os, sys, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from hbrig import Game, Pilot, SYMS, line_addr
TAP = TAPE
results = []
def check(name, ok, info=''):
    results.append((name, bool(ok))); print('%-58s %s %s' % (name, 'PASS' if ok else 'FAIL', info), flush=True)
ERRS = ('Error', 'No room', 'Syntax', 'No such', 'Break', 'line ', 'Out of', 'Overflow', 'Block', 'mismatch')
def errors(g): return [r for r in g.rows() if any(e in r for e in ERRS)]
def running(g): return g.s.regs()['PC'] != 0 and not (g.s.run_until.__self__ and False)

def footer(g): return 'SPACE  flap' in g.rows()[23] and 'BREAK  stop' in g.rows()[23]
def gap_rule(s): return max(52, 78 - 2 * s)
def space_rule(s): return max(24, 32 - (s >> 1))
class Spawns:
    """Watches the pipe table for each new pipe (a free slot being taken) and
    records (score on the screen, gap height, steps since the last pipe)."""
    def __init__(self, g): self.g = g; self.seen = set(); self.last = None; self.log = []
    def frame(self):
        g = self.g; p = SYMS['ptab']
        for k in range(4):
            used = g.peek(p + 4 * k) != 0x80
            if used and k not in self.seen:          # a free slot was just taken
                tk = g.tick(); gap = g.peek(p + 4 * k + 2) - g.peek(p + 4 * k + 1)
                self.log.append((g.score(), gap, None if self.last is None else (tk - self.last) & 255))
                self.last = tk; self.seen.add(k)
            elif not used: self.seen.discard(k)
    def bad(self):
        """pipes not matching the rule; the score may have just gone up by one
        in the same step, so either score is accepted.  A spacing is set by
        the score at the pipe before, and the step counter can be read a
        step early or late (a step can straddle a frame), so +-1 is allowed."""
        return [e for e in self.log if not (e[1] in (gap_rule(e[0]), gap_rule(e[0] - 1)) and
                (e[2] is None or any(abs(e[2] - space_rule(s)) <= 1 for s in (e[0], e[0] - 1, e[0] - 2))))]

def play(g):
    """from the title screen: SPACE starts a game"""
    g.tap(); g.frames(20)

# 1. the tape: LOAD "" on an empty machine, real tape signal
g = Game(tape=TAP); g.start('LOAD ""')
f = g.wait_text('Press SPACE to start', 6000)
check('tape: LOAD "" auto-runs, loads hbcode, shows the title', f is not None, '(%s frames, %.0f s)' % (f, (f or 0) / 50))
check('tape: CLEAR 59999 moved RAMTOP', (g.word(23730) & 0xFFFF) == 59999, str(g.word(23730) & 0xFFFF))
check('tape: hbcode is in memory (signature "HB")', g.peek(60014) == 72 and g.peek(60015) == 66)
check('tape: no error message on the title screen', not errors(g), str(errors(g)))
g.shot('/tmp/hb_t_title.png')

# 2. the title screen: the bat bobs, the ground scrolls, nothing else moves
ys = set(); gr = []
for i in range(40):
    g.frames(2); ys.add(g.y()); gr.append(g.peek(line_addr(180) + 5))
check('title: the bat bobs up and down', len(ys) >= 5, str(sorted(ys)))
check('title: the ground scrolls', len(set(gr)) > 1)
check('title: no pipes, title mode', g.pipes() == [] and g.peek(60013) == 0)
check('title: help text on the bottom row', footer(g), g.rows()[23].strip())

# 3. into play: gravity, from the bat at rest at the start of a game
g.space(True); hs = [(g.y(), g.v())]
g.frames(3); g.space(False)
for i in range(14):
    g.step(); hs.append((g.y(), g.v()))
check('play: SPACE starts a game, score 0', g.score() == 0 and g.peek(60013) == 1, g.rows()[0].strip())
check('play: no help text on the bottom row', g.rows()[23].strip() == '', repr(g.rows()[23].strip()))
dy = [hs[i + 1][0] - hs[i][0] for i in range(1, len(hs) - 1)]
check('gravity: with no key the bat falls, faster and faster', all(b >= a for a, b in zip(dy, dy[1:])) and dy[-1] > dy[0] and hs[-1][0] > hs[1][0], 'drops %s' % dy)
check('gravity: the fall speed is limited to vmax (20)', max(v for y, v in hs) == 20, str([v for y, v in hs]))

# 4. flap
y0 = g.y(); g.space(True); g.step(); g.step(); v1 = g.v(); y1 = g.y()
for i in range(10): g.step()
v2 = g.v(); g.space(False); g.step()
check('flap: SPACE sends the bat up', v1 < 0 and y1 < y0, 'y %d -> %d, speed %d' % (y0, y1, v1))
check('flap: holding SPACE flaps once only', v2 > 0, 'speed after 10 steps held %d' % v2)
# 5. ground: stop flapping
f = g.wait_text('G A M E', 2000)
check('ground: falling to the ground ends the game', f is not None and g.y() == 152, 'y %d' % g.y())
attr = g.peek(0x5800 + ((16 + 152) >> 3) * 32 + 8)
check('game over: the bat turns red', attr == 0x4A, hex(attr))
check('game over: score, best and prompt shown', g.has('Score  0') and g.has('SPACE to fly again'))
check('game over: help text back on the bottom row', footer(g), g.rows()[23].strip())
g.shot('/tmp/hb_t_ground.png')

# 6. restart, then the ceiling
g.frames(60); g.tap(); g.frames(20)
check('restart: SPACE plays again, the box is gone, score 0', g.score() == 0 and not g.has('G A M E') and g.peek(60013) == 1)
for i in range(400):
    if g.has('G A M E'): break
    g.tap(2); g.frames(2)
check('ceiling: flapping into the top ends the game', g.has('G A M E') and g.y() == 0, 'y %d' % g.y())

# 7. a pipe: fly level at one height until a pipe is in the way
g.frames(60); g.tap(); g.frames(20)
level = 146; since = 9            # low: below the bottom of any gap
for f in range(3000):
    if g.has('G A M E'): break
    since += 1
    if since == 2: g.space(False)
    if g.y() > level and g.v() >= 0 and since >= 4: g.space(True); since = 0
    g.frames(1)
g.space(False)
over = [p for p in g.pipes() if p[0] <= 19 and p[0] + 7 >= 16]
check('pipe: flying into a pipe ends the game', g.has('G A M E') and 0 < g.y() < 152 and over, 'y %d, pipes at the bat %s' % (g.y(), over))
g.shot('/tmp/hb_t_pipe.png')

# 8. scoring: a steady pilot; up to five games to reach 6 points (it usually does it in one)
best_seen = []; spawns = []
for aim in (6, 8, 5, 10, 7):
    g.space(False); g.frames(60); g.tap(); g.frames(20)
    p = Pilot(g, margin=aim); seen = [0]; sp = Spawns(g); spawns.append(sp)
    for f in range(20000):
        p.frame(); sp.frame()
        if f % 25 == 0:
            sc = g.score()
            if sc is not None and sc != seen[-1]: seen.append(sc)
            if sc == 3 and not best_seen: g.shot('/tmp/hb_t_score.png')
            if g.has('G A M E'): break
    g.frames(20); best_seen.append((seen, g.best()))
    if len(seen) >= 7: break
seen, best = best_seen[-1]
check('score: each pipe passed adds one point', seen == list(range(len(seen))) and len(seen) >= 7,
      'games %d, scores seen %s' % (len(best_seen), seen))
check('best: the best score is kept across games', best == max(max(s) for s, b in best_seen), 'best %s' % best)

# 9. endurance: ten more games in a row, then BREAK
games = 0; maxs = 0
for n in range(10):
    g.space(False); g.frames(60); g.tap(); g.frames(20)
    if g.score() != 0: break
    p = Pilot(g, margin=6 if n % 2 else 9); sp = Spawns(g); spawns.append(sp)
    for f in range(30000):
        p.frame(); sp.frame()
        if f % 100 == 0 and g.has('G A M E'): break
    if not g.has('G A M E') or errors(g): break
    games += 1; maxs = max(maxs, g.best())
check('endurance: 10 more games, restarting each time, no errors', games == 10 and not errors(g), '%d games, best %d' % (games, maxs))
log = [e for sp in spawns for e in sp.log]; bad = [e for sp in spawns for e in sp.bad()]
first = [sp.log[0] for sp in spawns if sp.log]
check('gap: the first pipe of every game has a 78-line gap', first and all(e[1] == 78 for e in first), '%d games' % len(first))
check('gap: 78 - 2 x score, never under 52; spacing 32 -> 24 steps', log and not bad,
      '%d pipes, gaps %s, spacings %s, wrong %s' % (len(log), sorted(set(e[1] for e in log), reverse=True),
      sorted(set(e[2] for e in log if e[2]), reverse=True), bad[:3]))
check('gap: narrowed to the 52-line minimum at a high score', any(e[1] == 52 for e in log) and min(e[1] for e in log) == 52,
      'smallest %d, top score %d' % (min(e[1] for e in log), max(e[0] for e in log)))
g.s.key('^'); g.s.key(' '); g.frames(20); g.s.key(' ', False); g.s.key('^', False); g.frames(20)
check('BREAK (CAPS+SPACE) stops the program with "Break"', g.has('Break'), str([r for r in g.rows() if 'Break' in r]))
def free_now(g):
    g.b.line('CLS'); g.b.line('PRINT FREE')
    nums = [r.strip() for r in g.rows() if r.strip().isdigit()]
    return int(nums[-1]) if nums else None
f13 = free_now(g)
g1 = Game(); g1.start(); g1.frames(150); g1.tap(); g1.wait_text('G A M E', 3000); g1.frames(20)
g1.s.key('^'); g1.s.key(' '); g1.frames(20); g1.s.key(' ', False); g1.s.key('^', False); g1.frames(20)
f1 = free_now(g1)
check('memory: FREE is the same after 1 game and after 13 (no leak)', f13 is not None and f13 == f1, 'FREE %s and %s bytes' % (f1, f13))

fails = [n for n, ok in results if not ok]
print('\n%d/%d passed' % (len(results) - len(fails), len(results)))
sys.exit(1 if fails else 0)
