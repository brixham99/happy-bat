#!/usr/bin/env python3
"""Check hbloader.bas in the OpticOS v1.0.1 rig: typed in and RUN, it must
leave exactly build/hbcode.bin at 60000 and SAVE the same bytes as "hbcode"
CODE 60000,1095.  Then a mistyped byte, two swapped bytes and a missing
line must each stop it with the right error."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from p3lib import Basic
from rig import decode_pulses
code = open(os.path.join(HB, 'build/hbcode.bin'), 'rb').read()
# an optional argument names another loader file (e.g. the 8-a-line one)
LOADER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HB, 'hbloader.bas')
src = [l.strip() for l in open(LOADER) if l.strip()]
print('loader file:', LOADER)
ok = True
def check(name, c, info=''):
    global ok; ok &= bool(c); print('%-55s %s %s' % (name, 'PASS' if c else 'FAIL', info))
def run(lines, save=False):
    b = Basic(); s = b.s
    b.enter(lines)
    if save: s.mic_start(3)
    b.line('RUN', 6_000_000_000)
    return b, s
b, s = run(src, True)
mem = bytes(s.peek(60000 + i) for i in range(len(code)))
check('loader: memory 60000-61094 equals hbcode.bin', mem == code)
got = decode_pulses(s.mic_pulses())
hdr, data = (got + [None, None])[:2]
check('loader: SAVE writes a CODE header "hbcode" 60000,1095',
      hdr is not None and hdr[1] == 3 and bytes(hdr[2:12]).rstrip() == b'hbcode' and
      hdr[12] | hdr[13] << 8 == len(code) and hdr[14] | hdr[15] << 8 == 60000, str(hdr and list(hdr[:16])))
check('loader: the saved data block equals hbcode.bin', data is not None and bytes(data[1:-1]) == code)
scr = '\n'.join(r for r in b.screen() if r.strip())
check('loader: reports "Code OK" and "Done", no error', 'Code OK' in scr and 'Done.' in scr and 'line' not in scr.split('Done.')[-1], scr.replace('\n', ' | ')[-120:])
# the tape made by mktape: same bytes as this?
tap = open(os.path.join(HB, 'happybat.tap'), 'rb').read()
check('loader: its block is the one on happybat.tap', bytes(data) in tap)
# errors
dl = [i for i, l in enumerate(src) if l.startswith('DATA ') and ',' in l]
i = dl[3]; parts = src[i].split(', '); at = parts[0].split()[1]
bad = list(src); p2 = list(parts); p2[5] = '$%02X' % ((int(p2[5][1:], 16) + 1) & 255); bad[i] = ', '.join(p2)
b, s = run(bad); scr = ' '.join(b.screen())
check('error: a mistyped byte -> "Check the line at %s"' % at, 'Check the line at ' + at in scr, scr.strip()[-80:])
bad = list(src); p2 = list(parts); p2[2], p2[3] = p2[3], p2[2]; bad[i] = ', '.join(p2)
assert p2[2] != p2[3]
b, s = run(bad); scr = ' '.join(b.screen())
check('error: two bytes swapped -> "Check the line at %s"' % at, 'Check the line at ' + at in scr, scr.strip()[-80:])
miss = src[dl[10]].split(',')[0].split()[1]
bad = list(src); del bad[dl[10]]
b, s = run(bad); scr = ' '.join(b.screen())
check('error: a missing line -> "DATA out of step at %s"' % miss, 'DATA out of step at ' + miss in scr, scr.strip()[-80:])
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
