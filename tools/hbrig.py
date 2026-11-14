"""Happy Bat test harness: the OpticOS v1.0.1 ROM in the OpticOS test rig
(tools/rig of the OpticOS repository, a Z80 + ULA emulator driven from
Python; see tools/paths.py).  The rig loads build/opticos.rom of that
repository, which must be the v1.0.1 release ROM (SHA-256 06961e1f...47a0c6)."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
import p3lib
from p3lib import Basic, SYM
SYMS = {}
for _l in open(os.path.join(HB, 'build', 'hbcode.sym')):
    _m = re.match(r'(\S+)\s+EQU\s+0?([0-9A-F]+)H', _l)
    if _m: SYMS[_m.group(1)] = int(_m.group(2), 16)

def prog():
    return [l.strip() for l in open(os.path.join(HB, 'happybat.bas')) if l.strip()]
def code():
    return open(os.path.join(HB, 'build', 'hbcode.bin'), 'rb').read()
def line_addr(y):
    return 0x4000 | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)

class Game:
    """tape=None: CLEAR 59999, put the code in memory, type the program in.
    tape=path: an empty machine with the tape in the deck (real signal)."""
    def __init__(self, tape=None):
        self.b = Basic(); self.s = self.b.s
        if tape:
            self.s.tape(tape)
        else:
            self.b.line('CLEAR 59999')
            self.s.load(60000, code())
            self.b.enter(prog())
    def start(self, text='RUN'):
        """type a line and press ENTER, without waiting for the prompt"""
        s = self.s
        assert s.run_until(SYM['cg_lp'], 20_000_000)
        s.load(p3lib.LINEBUF, text.encode()); s.poke(p3lib.CON_LEN, len(text))
        s.setregs(PC=SYM['con_enter'], SP=s.regs()['SP'] + 2)
    def frames(self, n): self.s.frame(n)
    def space(self, down): self.s.key(' ', down)
    def tap(self, hold=4):
        self.space(True); self.frames(hold); self.space(False)
    def rows(self): return self.b.screen()
    def has(self, text): return any(text in r for r in self.rows())
    def wait_text(self, text, limit):
        """run frames until text is on the screen; returns the frames taken, or None"""
        for f in range(0, limit, 10):
            if self.has(text): return f
            self.frames(10)
        return None
    def shot(self, path, scale=2): self.s.image(scale=scale).save(path)
    def peek(self, a): return self.s.peek(a)
    def word(self, a):
        v = self.s.peek(a) | self.s.peek(a + 1) << 8
        return v - 65536 if v >= 32768 else v
    def y(self): return self.peek(60009)
    def v(self): return self.word(SYMS['v16'])
    def tick(self): return self.peek(SYMS['tick'])
    def score(self):
        m = re.search(r'SCORE (\d+)', self.rows()[0]); return int(m.group(1)) if m else None
    def best(self):
        m = re.search(r'BEST (\d+)', self.rows()[0]); return int(m.group(1)) if m else None
    def pipes(self):
        """(x, gap top, gap bottom) of the pipes in use"""
        p = SYMS['ptab']
        return [(self.peek(p + 4 * k) - (256 if self.peek(p + 4 * k) > 127 else 0), self.peek(p + 4 * k + 1),
                 self.peek(p + 4 * k + 2)) for k in range(4) if self.peek(p + 4 * k) != 0x80]
    def step(self):
        """run frames until the machine code has finished one more step"""
        t = self.tick()
        for _ in range(10):
            self.frames(1)
            if self.tick() != t: return True
        return False

class Pilot:
    """Plays like a steady human.  It looks at the next pipe the bat has not
    yet passed (from the pipe table) and, using the game's own gravity,
    predicts where the bat will be two steps on if it does not flap; if that
    is within `margin` pixels of the bottom of the gap, it flaps.  With no
    pipe in sight it keeps to the middle.  SPACE is held 2 frames, then let
    go, like a tap."""
    def __init__(self, g, margin=6, wait=4):
        self.g = g; self.margin = margin; self.wait = wait; self.since = 99
    def floor(self):
        ahead = [p for p in self.g.pipes() if p[0] + 7 >= 14]
        if not ahead: return 100
        x, top, bot = min(ahead)
        return bot - 8 - self.margin
    def frame(self):
        g = self.g; self.since += 1
        if self.since == 2: g.space(False)
        y16, v = g.word(SYMS['y16']), g.v()
        gr, vm = g.peek(60016), g.peek(60018)
        for _ in range(2):
            v = min(v + gr, vm); y16 += v
        if y16 / 4 > self.floor() and self.since >= self.wait:
            g.space(True); self.since = 0
        g.frames(1)
