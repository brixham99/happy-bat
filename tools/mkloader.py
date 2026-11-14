#!/usr/bin/env python3
"""Make the type-in form of the Happy Bat machine code from build/hbcode.bin:
  hbloader.bas          an OpticBASIC loader: DATA lines, each with its address,
                        16 bytes in hex and a check number, then a total check;
                        it POKEs the code to 60000 and SAVEs it as "hbcode"
  build/hbcode_hex.txt  a hex dump with addresses
  build/manual_hbcode.md  both, as a section in the style of docs/manual/manual.md
The check number of a line is the sum of its bytes weighted 1, 2, 3 ... 16,
so a mistyped byte or two bytes swapped are both caught; the total is the
plain sum of all the bytes."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import HB
code = open(os.path.join(HB, 'build/hbcode.bin'), 'rb').read()
ORG, N = 60000, len(code)
# --per 8: 8 bytes a DATA line (narrow enough for the A5 manual), written
# with --out to another file; the default is 16 a line, to hbloader.bas.
args = sys.argv[1:]
PER = int(args[args.index('--per') + 1]) if '--per' in args else 16
OUT = args[args.index('--out') + 1] if '--out' in args else os.path.join(HB, 'hbloader.bas')
ONLY_LOADER = '--out' in args
END = ORG + N
def lines():
    for o in range(0, N, PER):
        chunk = code[o:o + PER]
        yield ORG + o, chunk, sum((i + 1) * b for i, b in enumerate(chunk))
data = ['DATA %d, %s, %d' % (a, ', '.join('$%02X' % b for b in c), k) for a, c, k in lines()]
assert max(len(l) for l in data) <= (64 if PER <= 8 else 120), max(len(l) for l in data)   # fits the 128-byte input line
total = sum(code)
EACH = ("' Each DATA line: its address, 16 bytes in hex ($C3 = 195), and\n' a check number: the bytes weighted 1, 2, 3 ... 16 and added."
        if PER == 16 else
        "' Each DATA line: its address, %d bytes in hex ($C3 = 195),\n' and a check number: the bytes weighted 1, 2, 3 ... %d, added." % (PER, PER))
loader = f"""' =============================================================
' HBCODE - type-in loader for Happy Bat's machine code
' Type this in and RUN it. It puts the {N:,} bytes of code at
' {ORG}-{END - 1}, checks every line, and saves them to tape
' as "hbcode" CODE {ORG},{N}, for happybat.bas to load.
{EACH}
' A wrong line stops the program with its address, so you can
' find it; the last DATA item is the sum of all the bytes.
' =============================================================
CLEAR {ORG - 1}
a = {ORG}: t = 0
REPEAT
  READ d
  IF d <> a THEN ERROR 200, "DATA out of step at " + STR$ a
  s = 0
  FOR i = 1 TO MIN({PER}, {END} - a)
    READ b: POKE a, b: a = a + 1
    s = s + i * b: t = t + b
  NEXT
  READ k
  IF k <> s THEN ERROR 201, "Check the line at " + STR$ d
UNTIL a = {END}
READ k
IF k <> t THEN ERROR 202, "Total wrong: " + STR$ t
PRINT "Code OK: {N} bytes at {ORG}."
PRINT "Saving hbcode. Start the tape."
SAVE "hbcode" CODE {ORG}, {N}
PRINT "Done."
""" + '\n'.join(data) + f'\nDATA {total}\n'
open(OUT, 'w').write(loader)
if ONLY_LOADER:
    print('%s: %d DATA lines of %d, longest %d chars' % (OUT, len(data), PER, max(map(len, data)))); sys.exit()
hexd = '\n'.join('%5d  %04X  ' % (ORG + o, ORG + o) + ' '.join('%02X' % b for b in code[o:o + 16])
                 for o in range(0, N, 16))
open(os.path.join(HB, 'build/hbcode_hex.txt'), 'w').write(hexd + '\n')
md = f"""## Typing in Happy Bat's machine code

Happy Bat keeps its fast parts in {N:,} bytes of machine code at {ORG}–{END - 1} (`${ORG:04X}`–`${END - 1:04X}`). The assembler source is `happybat.asm`. To make the `hbcode` tape block without an assembler, type in the program below and RUN it. It POKEs the bytes into place, checks them and saves them with `SAVE "hbcode" CODE {ORG}, {N}`.

The game expects its code to be the next block on the tape after the program, so make the tape in this order:

1. Type in `happybat.bas` and save it with `SAVE "happybat" AUTO start`.
2. Type `NEW`, then type in this loader and RUN it, with the tape still in place after the program.

After that, `LOAD ""` loads and runs the game, and the game loads its code.

Each DATA line holds its address, 16 bytes written in hex, and a check number. The check number is the line's bytes multiplied by 1, 2, 3 … 16 and added together, so it catches a wrong byte and two bytes swapped. If a line is wrong, the program stops with that line's address, for example "Check the line at 60016". The last DATA item is the sum of every byte.

```
{loader.rstrip()}
```

### Hex dump

The same bytes, 16 to a line, with each line's address in decimal and hex:

```
{hexd}
```
"""
open(os.path.join(HB, 'build/manual_hbcode.md'), 'w').write(md)
print('hbloader.bas: %d DATA lines, longest %d chars, total %d; hex dump %d lines' % (len(data), max(map(len, data)), total, hexd.count('\n') + 1))
