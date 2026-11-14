#!/usr/bin/env python3
"""Build happybat.tap / happybat.tzx with the OpticOS v1.0.1 ROM's own SAVE,
in the OpticOS test rig: the program is typed in and saved with
SAVE "happybat" AUTO start, then the machine code with
SAVE "hbcode" CODE 60000,<length>.  The MIC signal is decoded back into
tape blocks, so the tape holds exactly what the ROM writes."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
from p3lib import Basic
from rig import decode_pulses
code = open(os.path.join(HB, 'build/hbcode.bin'), 'rb').read()
prog = [l.strip() for l in open(os.path.join(HB, 'happybat.bas')) if l.strip()]
b = Basic(); s = b.s
b.line('CLEAR 59999')
s.load(60000, code)
b.enter(prog)
blocks = []
for cmd, kind in (('SAVE "happybat" AUTO start', 0), ('SAVE "hbcode" CODE 60000,%d' % len(code), 3)):
    s.mic_start(3)
    b.line(cmd, 4_000_000_000)
    got = decode_pulses(s.mic_pulses())
    assert len(got) == 2, (cmd, len(got))
    hdr, data = got
    assert hdr[0] == 0 and hdr[1] == kind and len(hdr) == 19, (cmd, hdr[:2])
    for blk in got:
        p = 0
        for x in blk[:-1]: p ^= x
        assert p == blk[-1], cmd                       # parity byte
    blocks += [bytes(hdr), bytes(data)]
    n = hdr[12] | hdr[13] << 8; p1 = hdr[14] | hdr[15] << 8
    print('%-28s %-10s %5d bytes  param1 %d' % (cmd, hdr[2:12].decode().rstrip(), n, p1))
assert blocks[1][1:5] == b'OB\x01\x00'                 # OpticBASIC program signature
assert blocks[3][1:-1] == code                         # the CODE block is the assembled code
tap = b''.join(struct.pack('<H', len(x)) + x for x in blocks)
open(os.path.join(HB, 'happybat.tap'), 'wb').write(tap)
tzx = b'ZXTape!\x1a\x01\x14' + b''.join(b'\x10' + struct.pack('<HH', 1000, len(x)) + x for x in blocks)
open(os.path.join(HB, 'happybat.tzx'), 'wb').write(tzx)
print('wrote happybat.tap (%d bytes) and happybat.tzx (%d bytes)' % (len(tap), len(tzx)))
