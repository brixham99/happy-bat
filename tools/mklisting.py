#!/usr/bin/env python3
"""Write happybat_listing.md: notes, memory map, then the full BASIC and
Z80 sources, read from the files so the listing always matches them."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import HB
bas = open(os.path.join(HB, 'happybat.bas')).read().rstrip('\n')
asm = open(os.path.join(HB, 'happybat.asm')).read().rstrip('\n')
code = open(os.path.join(HB, 'build/hbcode.bin'), 'rb').read()
sym = {m.group(1): int(m.group(2), 16) for m in
       (re.match(r'(\S+)\s+EQU\s+0?([0-9A-F]+)H', l) for l in open(os.path.join(HB, 'build/hbcode.sym'))) if m}
tap = os.path.getsize(os.path.join(HB, 'happybat.tap'))
_t = open(os.path.join(HB, 'happybat.tap'), 'rb').read()
prog_len = _t[14] | _t[15] << 8                # length field of the program's header
_s = os.path.join(HB, 'build/soak_results.txt')
soak = open(_s).read().strip() if os.path.exists(_s) and os.path.getsize(_s) else '(not run)'
manual = open(os.path.join(HB, 'build/manual_hbcode.md')).read().strip()
end = 60000 + len(code) - 1
def a(n): return '%d ($%04X)' % (sym[n], sym[n])
NOTES = f'''# Happy Bat: full listing

A Flappy Bird-style game for **OpticOS v1.0.1 / OpticBASIC** on a 48K machine.
It is written from scratch (clean room); no Sinclair ROM code is used or called.

| File | What it is |
|---|---|
| `happybat.bas` | the OpticBASIC program (no line numbers, named PROCs, no GOTO/GOSUB) |
| `happybat.asm` | the Z80 machine code (pasmo) |
| `build/hbcode.bin`, `build/hbcode.sym` | the assembled code and its symbols |
| `happybat.tap` ({tap:,} bytes), `happybat.tzx` | the tape: program `happybat` (AUTO start) + `hbcode` CODE 60000,{len(code)} |
| `shots/*.png` | screenshots from Fuse running the v1.0.1 ROM |
| `hbloader.bas` | type-in OpticBASIC loader for the machine code (made by `tools/mkloader.py` from `build/hbcode.bin`) |
| `build/hbcode_hex.txt`, `build/manual_hbcode.md` | hex dump; the type-in section in the manual's style (below) |
| `tools/` | build and test scripts (tape builder, loader maker, rig test suites, Fuse scripts) |

## Controls and loading

* **SPACE**: start a game, flap the bat's wings, play again after a game over.
* **BREAK** (CAPS SHIFT + SPACE): stop the program (OpticBASIC reports `Break`).

Load it with `LOAD ""` and start the tape. The program auto-runs: its first
lines `CLEAR 59999` and then `LOAD "hbcode" CODE` (only if the code is not in memory already,
checked by the "HB" signature at 60014). The title screen follows. Nothing has to be typed after `LOAD ""`.

## How the two halves fit together

OpticBASIC runs the game: the title screen, when pipes appear and where their gaps
are, the score and best score, the game-over box, and restarting. Each step, the
machine code does the work that touches thousands of screen bytes: it scrolls the ground,
moves and draws up to four pipes, reads the flap key, applies gravity, and moves, draws and
collision-tests the bat.

OpticBASIC's `CALL` and `USR` take no register arguments, so the interface is a
parameter block that BASIC POKEs, plus the result of `USR`, which is the BC register:

| Address | Name | Use |
|---|---|---|
| 60000 | `init` | `CALL 60000`: new playfield (clear, colour, ground, no pipes, the bat at rest at line PEEK 60009) |
| 60003 | `step` | `r% = USR 60003`: one step; 0 = flying, 1 = crashed, 2 = a pipe passed (a point) |
| 60006 | `dead` | `CALL 60006`: turn the bat red |
| 60009 | `baty` | the bat's top line, 0-152 (BASIC sets it on the title; the code moves it in play) |
| 60010 / 60011 | `gaptop` / `gapbot` | the next pipe's gap: its first line and the first line below it |
| 60012 | `newpipe` | POKE 1: start that pipe at the right-hand edge |
| 60013 | `mode` | 1 = play; 0 = title (the ground scrolls and the bat bobs, with no gravity or pipes) |
| 60014-15 | `sig` | "HB": the code is loaded |
| 60016-19 | `grav`, `flapv`, `vmax`, `pacev` | gravity 2, flap 18, fastest fall 20 (quarter pixels a step), 2 frames a step |

The loop in PROC `play` is only four statements a step: `r% = USR 60003`, a countdown that calls
`new_pipe` when it reaches 0, and `point` when r% = 2. That keeps BASIC well inside the 2-frame step.

**Difficulty.** The game starts easy and tightens as the score rises (PROC `new_pipe`):

| Score | Gap height (lines) | Steps to the next pipe (pixels apart) |
|---|---|---|
| 0 | 78 | 32 (128) |
| 1 | 76 | 32 |
| 4 | 70 | 30 (120) |
| 8 | 62 | 28 (112) |
| 13 and over | 52 (the minimum) | 26 (104) |
| 16 and over | 52 | 24 (96, the minimum) |

The gap is `MAX(52, 78 - 2 * score%)`, and the spacing is `MAX(24, 32 - (score% >> 1))`. (The first version used a gap of 52 down to 36 and a fixed 24 steps.)
The bat is 8 lines tall, and a pipe is 32 pixels wide.

The step itself (`step`) does the following: it waits until `pacev` frames have passed (HALT, FRAMES at 23672), XORs the bat off, applies physics
(edge-detected SPACE from port $7FFE, a short chirp on the speaker, gravity, a speed limit, ceiling and
ground crashes), moves and redraws the pipes (8 nibbles = 32 pixels wide, with caps above and below
the gap, clipped at both screen edges), scrolls the ground with RLD, then tests the bat against
the screen with AND before XORing it on (a pipe hit = a crash). The worst step takes about 107,000 T-states
(1.5 frames) with three pipes on the screen, so the game runs at about 23 steps a second (mostly 2 frames a step) at
4 pixels a step. The code does not use IX, IY or the alternate registers; the interpreter needs them.

## Screen layout (64-column mode)

| Lines | Character row | Contents |
|---|---|---|
| 0-7 | 0 | score line: HAPPY BAT / SCORE / BEST (BASIC) |
| 8-15 | 1 | blank |
| 16-175 | 2-21 | playfield: sky (blue, green ink for the pipes), the bat at x 64-79 in yellow |
| 176-183 | 22 | the ground, scrolling (green and yellow) |
| 184-191 | 23 | help: "SPACE  flap" / "BREAK  stop", on the title and game-over screens only (empty in play) |

## Memory map (48K)

| Address | Contents |
|---|---|
| 0-16383 | OpticOS v1.0.1 ROM |
| 16384-23295 | screen and attributes |
| 23296-59999 | OpticOS system area, the BASIC program ({prog_len:,} bytes saved), variables, string heap and stacks. RAMTOP = 59999 (`CLEAR 59999`) |
| 60000-60019 | jump table and parameter block |
| 60020-{sym["pg1"]-1} | internal state (`y16`, `v16`, `pkey`, `oldy`, `oldspr`, `drawn`, `tick`, `phase`, `lastf`, `crash`, `scored`, the pipe table `ptab` at {sym["ptab"]}: 4 slots x 4 bytes) |
| {sym["pg1"]}-{sym["init"]-1} | the pipe-drawing working variables |
| {sym["init"]}-{sym["spr_up"]-1} | code |
| {sym["spr_up"]}-{end} | sprites (two wing frames, 16x8), the ground pattern and the pipe patterns |
| {end+1}-65535 | not used by Happy Bat |

The machine code is **{len(code):,} bytes** ({60000}-{end}). With the program loaded and after any number
of games, `PRINT FREE` reports **25,462 bytes** free.

## OpticBASIC limits met, and what was done about them

* **Speed.** An OpticBASIC statement takes roughly a sixth of a frame, so BASIC alone could not move pipes and a bat
  smoothly. Everything per-pixel went into machine code, and the BASIC loop was kept to four statements.
* **No register arguments to CALL/USR** (cut from v1.0.1). Values are POKEd into the parameter block, and results come back in BC through USR.
* **A comment after a statement needs a colon**: `x = 1: ' note`. A bare trailing `'` is a syntax error.
* **A block IF has no THEN.** `IF cond` on its own line opens a block; `IF cond THEN …` is the one-line form. Writing THEN on a block IF gives "Block structure".
* **The string heap is only tidied when space runs out.** The first version printed `STRING$(28, " ")` eight times per game over, and FREE fell
  by 248 bytes a game. It would have been reclaimed eventually, but the string is now made once (`box$`), so FREE stays the same.
* **AUTO start runs a PROC**, so PROC `start` simply does `RUN`, and the program begins at the top, where `CLEAR 59999` belongs.
* **Colour clash.** The attribute map has one ink per 8x8 cell, so a pipe's pixels inside the bat's cells turn yellow while the bat is there. This is the usual
  Spectrum look and was left as it is.

## Tests

* The rig suite, `tools/test_happybat.py` (the v1.0.1 ROM in the OpticOS Z80 test rig, loading the real tape signal), passes 29/29. It covers
  the tape auto-run, RAMTOP and the code; the title bob and ground scroll; gravity and the fall-speed limit; flap, and a held key
  flapping only once; crashes into the ground, ceiling and a pipe; the game-over screen; restart; the score counting up one pipe at a time;
  the best score; 10 more games; the gap and spacing of every new pipe (534 pipes; 78 lines first, down to 52; 32 down to 24 steps); the help row shown on the title and game-over screens and empty in play; BREAK; and FREE the same after 1 and 13 games. The results are in `build/test_results.txt`.
* A soak test, `tools/t_soak.py`: {soak}
* The type-in loader, `tools/test_loader.py`: typed in and RUN, `hbloader.bas` leaves exactly `hbcode.bin` at 60000, and its SAVE writes the same header and bytes as the `hbcode` block on `happybat.tap`. A mistyped byte, two swapped bytes and a missing DATA line each stop it with the right message.
* Fuse 1.6 (`fuse-sdl`, 48K, the v1.0.1 release ROM). `LOAD ""` with tape traps off (the real tape signal) and on both auto-run to the title.
  `tools/fuse_play.py` plays in a slowed Fuse, reading the screen and pressing SPACE with xdotool; it scored 7 and took the screenshots in `shots/`.

## Rebuilding

The tools need a checkout of [OpticOS](https://github.com/brixham99/OpticOS), for its Z80 test rig and Fuse helpers, with the v1.0.1 ROM at `build/opticos.rom` in it. Point `OPTICOS_REPO` at that checkout; it defaults to a folder `OpticOS` next to this one. `OPTICOS_ROM` can name a different ROM file for Fuse. No ROM is included here.

    pasmo --bin happybat.asm build/hbcode.bin build/hbcode.sym
    python3 tools/mkloader.py        # hbloader.bas, the hex dump and the manual section
    python3 tools/mktape.py          # types the program into the ROM and SAVEs both blocks -> happybat.tap/.tzx
    python3 tools/mklisting.py       # this file
    python3 tools/test_happybat.py   # rig tests

'''
open(os.path.join(HB, 'happybat_listing.md'), 'w').write(
    NOTES + '# The machine code as a type-in listing (for the OpticOS manual)\n\nThis section is written to drop into `docs/manual/manual.md`.\n\n' + manual.replace('\n## ', '\n## ', 1) + '\n\n# Sources\n\n## happybat.bas\n\n```basic\n' + bas + '\n```\n\n## happybat.asm\n\n```asm\n' + asm + '\n```\n')
print('wrote happybat_listing.md')
