# Happy Bat: full listing

A Flappy Bird-style game for **OpticOS v1.0.1 / OpticBASIC** on a 48K machine.
It is written from scratch (clean room); no Sinclair ROM code is used or called.

| File | What it is |
|---|---|
| `happybat.bas` | the OpticBASIC program (no line numbers, named PROCs, no GOTO/GOSUB) |
| `happybat.asm` | the Z80 machine code (pasmo) |
| `build/hbcode.bin`, `build/hbcode.sym` | the assembled code and its symbols |
| `happybat.tap` (6,652 bytes), `happybat.tzx` | the tape: program `happybat` (AUTO start) + `hbcode` CODE 60000,1095 |
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
| 23296-59999 | OpticOS system area, the BASIC program (5,507 bytes saved), variables, string heap and stacks. RAMTOP = 59999 (`CLEAR 59999`) |
| 60000-60019 | jump table and parameter block |
| 60020-60049 | internal state (`y16`, `v16`, `pkey`, `oldy`, `oldspr`, `drawn`, `tick`, `phase`, `lastf`, `crash`, `scored`, the pipe table `ptab` at 60034: 4 slots x 4 bytes) |
| 60050-60060 | the pipe-drawing working variables |
| 60061-60994 | code |
| 60995-61094 | sprites (two wing frames, 16x8), the ground pattern and the pipe patterns |
| 61095-65535 | not used by Happy Bat |

The machine code is **1,095 bytes** (60000-61094). With the program loaded and after any number
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
* A soak test, `tools/t_soak.py`: 40 games, scores [0, 34, 0, 17, 0, 50, 0, 20, 0, 50, 0, 49, 0, 20, 0, 50, 0, 17, 0, 32, 0, 50, 0, 50, 0, 42, 0, 26, 0, 50, 0, 50, 0, 22, 0, 33, 0, 50, 0, 50] errors 0 FREE 25462
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

# The machine code as a type-in listing (for the OpticOS manual)

This section is written to drop into `docs/manual/manual.md`.

## Typing in Happy Bat's machine code

Happy Bat keeps its fast parts in 1,095 bytes of machine code at 60000–61094 (`$EA60`–`$EEA6`). The assembler source is `happybat.asm`. To make the `hbcode` tape block without an assembler, type in the program below and RUN it. It POKEs the bytes into place, checks them and saves them with `SAVE "hbcode" CODE 60000, 1095`.

The game expects its code to be the next block on the tape after the program, so make the tape in this order:

1. Type in `happybat.bas` and save it with `SAVE "happybat" AUTO start`.
2. Type `NEW`, then type in this loader and RUN it, with the tape still in place after the program.

After that, `LOAD ""` loads and runs the game, and the game loads its code.

Each DATA line holds its address, 16 bytes written in hex, and a check number. The check number is the line's bytes multiplied by 1, 2, 3 … 16 and added together, so it catches a wrong byte and two bytes swapped. If a line is wrong, the program stops with that line's address, for example "Check the line at 60016". The last DATA item is the sum of every byte.

```
' =============================================================
' HBCODE - type-in loader for Happy Bat's machine code
' Type this in and RUN it. It puts the 1,095 bytes of code at
' 60000-61094, checks every line, and saves them to tape
' as "hbcode" CODE 60000,1095, for happybat.bas to load.
' Each DATA line: its address, 16 bytes in hex ($C3 = 195), and
' a check number: the bytes weighted 1, 2, 3 ... 16 and added.
' A wrong line stops the program with its address, so you can
' find it; the last DATA item is the sum of all the bytes.
' =============================================================
CLEAR 59999
a = 60000: t = 0
REPEAT
  READ d
  IF d <> a THEN ERROR 200, "DATA out of step at " + STR$ a
  s = 0
  FOR i = 1 TO MIN(16, 61095 - a)
    READ b: POKE a, b: a = a + 1
    s = s + i * b: t = t + b
  NEXT
  READ k
  IF k <> s THEN ERROR 201, "Check the line at " + STR$ d
UNTIL a = 61095
READ k
IF k <> t THEN ERROR 202, "Total wrong: " + STR$ t
PRINT "Code OK: 1095 bytes at 60000."
PRINT "Saving hbcode. Start the tape."
SAVE "hbcode" CODE 60000, 1095
PRINT "Done."
DATA 60000, $C3, $9D, $EA, $C3, $22, $EB, $C3, $CC, $ED, $48, $28, $58, $00, $01, $48, $42, 13067
DATA 60016, $02, $12, $14, $02, $20, $01, $00, $00, $00, $00, $43, $EE, $00, $00, $00, $00, 3865
DATA 60032, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, $80, 17024
DATA 60048, $80, $80, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $0E, $10, $79, 2756
DATA 60064, $CD, $14, $EE, $06, $20, $AF, $77, $2C, $10, $FC, $0C, $79, $FE, $C0, $20, $EF, 17920
DATA 60080, $21, $40, $58, $01, $80, $02, $3E, $4C, $CD, $38, $EE, $21, $C0, $5A, $01, $20, 11825
DATA 60096, $00, $3E, $66, $CD, $38, $EE, $21, $E0, $5A, $01, $20, $00, $3E, $60, $CD, $38, 12274
DATA 60112, $EE, $11, $83, $EE, $0E, $B0, $79, $CD, $14, $EE, $06, $10, $1A, $77, $2C, $13, 11016
DATA 60128, $1A, $77, $2C, $1B, $10, $F6, $13, $13, $0C, $79, $FE, $B8, $20, $E8, $21, $82, 14904
DATA 60144, $EA, $01, $10, $00, $3E, $80, $CD, $38, $EE, $AF, $32, $7C, $EA, $32, $7D, $EA, 18536
DATA 60160, $32, $7E, $EA, $32, $6C, $EA, $67, $6F, $22, $76, $EA, $3C, $32, $6D, $EA, $32, 16023
DATA 60176, $78, $EA, $3A, $69, $EA, $6F, $29, $29, $22, $74, $EA, $3A, $78, $5C, $32, $7F, 13999
DATA 60192, $EA, $C9, $CD, $5D, $EB, $CD, $B1, $ED, $AF, $32, $80, $EA, $32, $81, $EA, $3A, 20348
DATA 60208, $6D, $EA, $B7, $28, $06, $CD, $74, $EB, $CD, $F5, $EB, $CD, $FA, $EC, $21, $7D, 23627
DATA 60224, $EA, $34, $CD, $87, $ED, $79, $B7, $28, $03, $32, $80, $EA, $01, $01, $00, $3A, 10703
DATA 60240, $80, $EA, $B7, $C0, $0C, $3A, $81, $EA, $B7, $C0, $0E, $00, $C9, $21, $7F, $EA, 17541
DATA 60256, $3A, $78, $5C, $96, $47, $3A, $73, $EA, $3D, $B8, $38, $03, $76, $18, $F1, $3A, 14008
DATA 60272, $78, $5C, $77, $C9, $3E, $7F, $DB, $FE, $2F, $E6, $01, $21, $78, $EA, $46, $77, 17022
DATA 60288, $28, $11, $05, $28, $0E, $3A, $71, $EA, $ED, $44, $6F, $26, $FF, $22, $76, $EA, 17125
DATA 60304, $CD, $E1, $EB, $2A, $76, $EA, $3A, $70, $EA, $5F, $16, $00, $19, $CB, $7C, $20, 13661
DATA 60320, $0D, $3A, $72, $EA, $5F, $7C, $B7, $20, $04, $7D, $BB, $38, $01, $EB, $22, $76, 13879
DATA 60336, $EA, $ED, $5B, $74, $EA, $19, $CB, $7C, $28, $05, $21, $00, $00, $18, $0D, $E5, 10146
DATA 60352, $11, $61, $02, $B7, $ED, $52, $E1, $38, $08, $21, $60, $02, $3E, $01, $32, $80, 9749
DATA 60368, $EA, $22, $74, $EA, $CB, $3C, $CB, $1D, $CB, $3C, $CB, $1D, $7D, $32, $69, $EA, 17266
DATA 60384, $C9, $06, $18, $78, $E6, $01, $07, $07, $07, $07, $D3, $FE, $78, $C6, $08, $3D, 12956
DATA 60400, $20, $FD, $10, $EF, $C9, $3A, $6C, $EA, $B7, $28, $22, $AF, $32, $6C, $EA, $21, 16244
DATA 60416, $82, $EA, $11, $04, $00, $06, $04, $7E, $FE, $80, $28, $05, $19, $10, $F8, $18, 10456
DATA 60432, $0C, $36, $40, $23, $3A, $6A, $EA, $77, $23, $3A, $6B, $EA, $77, $21, $82, $EA, 16551
DATA 60448, $06, $04, $C5, $E5, $CD, $30, $EC, $E1, $11, $04, $00, $19, $C1, $10, $F3, $C9, 16373
DATA 60464, $7E, $FE, $80, $C8, $3D, $77, $FE, $08, $20, $06, $3E, $01, $32, $81, $EA, $7E, 13703
DATA 60480, $C6, $08, $FE, $49, $38, $03, $36, $80, $C9, $23, $7E, $32, $92, $EA, $23, $7E, 14828
DATA 60496, $32, $93, $EA, $2B, $2B, $7E, $11, $93, $EE, $01, $9D, $EE, $CB, $47, $28, $06, 14548
DATA 60512, $11, $98, $EE, $01, $A2, $EE, $ED, $53, $97, $EA, $ED, $43, $99, $EA, $CB, $2F, 21772
DATA 60528, $0E, $05, $CB, $7F, $28, $18, $ED, $44, $47, $79, $90, $4F, $58, $16, $00, $2A, 10193
DATA 60544, $97, $EA, $19, $22, $97, $EA, $2A, $99, $EA, $19, $22, $99, $EA, $AF, $32, $94, 17683
DATA 60560, $EA, $81, $D6, $20, $38, $06, $47, $79, $90, $C8, $D8, $4F, $79, $32, $95, $EA, 17915
DATA 60576, $2A, $97, $EA, $22, $9B, $EA, $3A, $92, $EA, $D6, $04, $47, $AF, $CD, $DC, $EC, 22298
DATA 60592, $2A, $99, $EA, $22, $9B, $EA, $3A, $92, $EA, $D6, $04, $06, $04, $CD, $DC, $EC, 19299
DATA 60608, $3A, $93, $EA, $06, $04, $CD, $DC, $EC, $2A, $97, $EA, $22, $9B, $EA, $3A, $93, 19139
DATA 60624, $EA, $C6, $04, $4F, $3E, $A0, $91, $47, $79, $C3, $DC, $EC, $C6, $10, $CD, $14, 18295
DATA 60640, $EE, $3A, $94, $EA, $B5, $6F, $C5, $E5, $EB, $2A, $9B, $EA, $ED, $4B, $95, $EA, 23674
DATA 60656, $ED, $B0, $E1, $CD, $29, $EE, $C1, $10, $ED, $C9, $3A, $7E, $EA, $5F, $16, $00, 16191
DATA 60672, $21, $63, $EE, $19, $EB, $0E, $B0, $79, $CD, $14, $EE, $7D, $F6, $1F, $6F, $1A, 16380
DATA 60688, $CD, $27, $ED, $13, $13, $13, $13, $0C, $79, $FE, $B8, $20, $EA, $3A, $7E, $EA, 17033
DATA 60704, $3C, $E6, $03, $32, $7E, $EA, $C9, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, 17742
DATA 60720, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, 18552
DATA 60736, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, 18126
DATA 60752, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, 16770
DATA 60768, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, 18552
DATA 60784, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, $2D, $ED, $6F, 18126
DATA 60800, $2D, $ED, $6F, $2D, $ED, $6F, $C9, $3A, $7D, $EA, $E6, $02, $21, $43, $EE, $28, 16350
DATA 60816, $03, $21, $53, $EE, $22, $7A, $EA, $EB, $3A, $69, $EA, $32, $79, $EA, $CD, $D4, 21752
DATA 60832, $ED, $C5, $3A, $79, $EA, $1E, $4E, $CD, $F8, $ED, $3E, $01, $32, $7C, $EA, $C1, 19105
DATA 60848, $C9, $3A, $7C, $EA, $B7, $C8, $AF, $32, $7C, $EA, $ED, $5B, $7A, $EA, $3A, $79, 20188
DATA 60864, $EA, $CD, $D4, $ED, $3A, $79, $EA, $1E, $4C, $C3, $F8, $ED, $3A, $79, $EA, $1E, 19766
DATA 60880, $4A, $C3, $F8, $ED, $C6, $10, $06, $08, $0E, $00, $F5, $CD, $14, $EE, $7D, $F6, 18032
DATA 60896, $08, $6F, $1A, $A6, $B1, $4F, $1A, $AE, $77, $13, $2C, $1A, $A6, $B1, $4F, $1A, 12199
DATA 60912, $AE, $77, $13, $F1, $3C, $10, $E3, $C9, $C6, $10, $F5, $CD, $01, $EE, $F1, $C6, 22251
DATA 60928, $07, $E6, $F8, $6F, $26, $00, $29, $29, $7C, $C6, $58, $67, $7D, $F6, $08, $6F, 14725
DATA 60944, $73, $2C, $73, $C9, $6F, $E6, $07, $F6, $40, $67, $7D, $1F, $1F, $1F, $E6, $18, 13328
DATA 60960, $B4, $67, $7D, $17, $17, $E6, $E0, $6F, $C9, $24, $7C, $E6, $07, $C0, $7D, $C6, 18919
DATA 60976, $20, $6F, $D8, $7C, $D6, $08, $67, $C9, $77, $0B, $78, $B1, $C8, $54, $5D, $13, 14945
DATA 60992, $ED, $B0, $C9, $04, $20, $87, $E1, $C5, $A3, $EF, $F7, $7D, $BE, $3E, $7C, $0F, 18841
DATA 61008, $F0, $02, $40, $04, $20, $07, $E0, $05, $A0, $7F, $FE, $FF, $FF, $ED, $B7, $CE, 23500
DATA 61024, $73, $83, $C1, $0F, $0F, $0F, $0F, $08, $03, $08, $03, $00, $0E, $00, $0E, $03, 1930
DATA 61040, $08, $03, $08, $0E, $00, $0E, $00, $08, $03, $08, $03, $00, $0E, $00, $0E, $08, 902
DATA 61056, $08, $08, $08, $FF, $FF, $83, $83, $0E, $0E, $38, $38, $E0, $E0, $83, $83, $0E, 15083
DATA 61072, $0E, $88, $88, $0F, $BF, $FF, $E0, $00, $00, $FB, $FF, $FE, $00, $7F, $BF, $FF, 21893
DATA 61088, $FE, $00, $07, $FB, $FF, $FF, $E0, 5652
DATA 128134
```

### Hex dump

The same bytes, 16 to a line, with each line's address in decimal and hex:

```
60000  EA60  C3 9D EA C3 22 EB C3 CC ED 48 28 58 00 01 48 42
60016  EA70  02 12 14 02 20 01 00 00 00 00 43 EE 00 00 00 00
60032  EA80  00 00 80 80 80 80 80 80 80 80 80 80 80 80 80 80
60048  EA90  80 80 00 00 00 00 00 00 00 00 00 00 00 0E 10 79
60064  EAA0  CD 14 EE 06 20 AF 77 2C 10 FC 0C 79 FE C0 20 EF
60080  EAB0  21 40 58 01 80 02 3E 4C CD 38 EE 21 C0 5A 01 20
60096  EAC0  00 3E 66 CD 38 EE 21 E0 5A 01 20 00 3E 60 CD 38
60112  EAD0  EE 11 83 EE 0E B0 79 CD 14 EE 06 10 1A 77 2C 13
60128  EAE0  1A 77 2C 1B 10 F6 13 13 0C 79 FE B8 20 E8 21 82
60144  EAF0  EA 01 10 00 3E 80 CD 38 EE AF 32 7C EA 32 7D EA
60160  EB00  32 7E EA 32 6C EA 67 6F 22 76 EA 3C 32 6D EA 32
60176  EB10  78 EA 3A 69 EA 6F 29 29 22 74 EA 3A 78 5C 32 7F
60192  EB20  EA C9 CD 5D EB CD B1 ED AF 32 80 EA 32 81 EA 3A
60208  EB30  6D EA B7 28 06 CD 74 EB CD F5 EB CD FA EC 21 7D
60224  EB40  EA 34 CD 87 ED 79 B7 28 03 32 80 EA 01 01 00 3A
60240  EB50  80 EA B7 C0 0C 3A 81 EA B7 C0 0E 00 C9 21 7F EA
60256  EB60  3A 78 5C 96 47 3A 73 EA 3D B8 38 03 76 18 F1 3A
60272  EB70  78 5C 77 C9 3E 7F DB FE 2F E6 01 21 78 EA 46 77
60288  EB80  28 11 05 28 0E 3A 71 EA ED 44 6F 26 FF 22 76 EA
60304  EB90  CD E1 EB 2A 76 EA 3A 70 EA 5F 16 00 19 CB 7C 20
60320  EBA0  0D 3A 72 EA 5F 7C B7 20 04 7D BB 38 01 EB 22 76
60336  EBB0  EA ED 5B 74 EA 19 CB 7C 28 05 21 00 00 18 0D E5
60352  EBC0  11 61 02 B7 ED 52 E1 38 08 21 60 02 3E 01 32 80
60368  EBD0  EA 22 74 EA CB 3C CB 1D CB 3C CB 1D 7D 32 69 EA
60384  EBE0  C9 06 18 78 E6 01 07 07 07 07 D3 FE 78 C6 08 3D
60400  EBF0  20 FD 10 EF C9 3A 6C EA B7 28 22 AF 32 6C EA 21
60416  EC00  82 EA 11 04 00 06 04 7E FE 80 28 05 19 10 F8 18
60432  EC10  0C 36 40 23 3A 6A EA 77 23 3A 6B EA 77 21 82 EA
60448  EC20  06 04 C5 E5 CD 30 EC E1 11 04 00 19 C1 10 F3 C9
60464  EC30  7E FE 80 C8 3D 77 FE 08 20 06 3E 01 32 81 EA 7E
60480  EC40  C6 08 FE 49 38 03 36 80 C9 23 7E 32 92 EA 23 7E
60496  EC50  32 93 EA 2B 2B 7E 11 93 EE 01 9D EE CB 47 28 06
60512  EC60  11 98 EE 01 A2 EE ED 53 97 EA ED 43 99 EA CB 2F
60528  EC70  0E 05 CB 7F 28 18 ED 44 47 79 90 4F 58 16 00 2A
60544  EC80  97 EA 19 22 97 EA 2A 99 EA 19 22 99 EA AF 32 94
60560  EC90  EA 81 D6 20 38 06 47 79 90 C8 D8 4F 79 32 95 EA
60576  ECA0  2A 97 EA 22 9B EA 3A 92 EA D6 04 47 AF CD DC EC
60592  ECB0  2A 99 EA 22 9B EA 3A 92 EA D6 04 06 04 CD DC EC
60608  ECC0  3A 93 EA 06 04 CD DC EC 2A 97 EA 22 9B EA 3A 93
60624  ECD0  EA C6 04 4F 3E A0 91 47 79 C3 DC EC C6 10 CD 14
60640  ECE0  EE 3A 94 EA B5 6F C5 E5 EB 2A 9B EA ED 4B 95 EA
60656  ECF0  ED B0 E1 CD 29 EE C1 10 ED C9 3A 7E EA 5F 16 00
60672  ED00  21 63 EE 19 EB 0E B0 79 CD 14 EE 7D F6 1F 6F 1A
60688  ED10  CD 27 ED 13 13 13 13 0C 79 FE B8 20 EA 3A 7E EA
60704  ED20  3C E6 03 32 7E EA C9 ED 6F 2D ED 6F 2D ED 6F 2D
60720  ED30  ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED
60736  ED40  6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F
60752  ED50  2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D
60768  ED60  ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED
60784  ED70  6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F 2D ED 6F
60800  ED80  2D ED 6F 2D ED 6F C9 3A 7D EA E6 02 21 43 EE 28
60816  ED90  03 21 53 EE 22 7A EA EB 3A 69 EA 32 79 EA CD D4
60832  EDA0  ED C5 3A 79 EA 1E 4E CD F8 ED 3E 01 32 7C EA C1
60848  EDB0  C9 3A 7C EA B7 C8 AF 32 7C EA ED 5B 7A EA 3A 79
60864  EDC0  EA CD D4 ED 3A 79 EA 1E 4C C3 F8 ED 3A 79 EA 1E
60880  EDD0  4A C3 F8 ED C6 10 06 08 0E 00 F5 CD 14 EE 7D F6
60896  EDE0  08 6F 1A A6 B1 4F 1A AE 77 13 2C 1A A6 B1 4F 1A
60912  EDF0  AE 77 13 F1 3C 10 E3 C9 C6 10 F5 CD 01 EE F1 C6
60928  EE00  07 E6 F8 6F 26 00 29 29 7C C6 58 67 7D F6 08 6F
60944  EE10  73 2C 73 C9 6F E6 07 F6 40 67 7D 1F 1F 1F E6 18
60960  EE20  B4 67 7D 17 17 E6 E0 6F C9 24 7C E6 07 C0 7D C6
60976  EE30  20 6F D8 7C D6 08 67 C9 77 0B 78 B1 C8 54 5D 13
60992  EE40  ED B0 C9 04 20 87 E1 C5 A3 EF F7 7D BE 3E 7C 0F
61008  EE50  F0 02 40 04 20 07 E0 05 A0 7F FE FF FF ED B7 CE
61024  EE60  73 83 C1 0F 0F 0F 0F 08 03 08 03 00 0E 00 0E 03
61040  EE70  08 03 08 0E 00 0E 00 08 03 08 03 00 0E 00 0E 08
61056  EE80  08 08 08 FF FF 83 83 0E 0E 38 38 E0 E0 83 83 0E
61072  EE90  0E 88 88 0F BF FF E0 00 00 FB FF FE 00 7F BF FF
61088  EEA0  FE 00 07 FB FF FF E0
```

# Sources

## happybat.bas

```basic
' =============================================================
' HAPPY BAT - a Flappy Bird-style game for OpticOS v1.0.1
' OpticBASIC runs the game: title, pipes and their gaps, score,
' best score, game over and restart. A machine-code block
' "hbcode" (60000-61094, source happybat.asm) does the work that
' touches thousands of screen bytes each step: scrolling the
' ground, moving and drawing the pipes, and moving, drawing and
' testing the bat, with gravity and the flap key.
'
' Machine code, called with CALL / USR. They take no register
' arguments, so BASIC POKEs what the code needs first:
'   CALL 60000      new playfield: clear, colour, draw ground;
'                   the bat starts at line PEEK 60009, at rest
'   r% = USR 60003  one step: 0 = flying, 1 = crashed, 2 = a
'                   pipe got past the bat (a point)
'   CALL 60006      colour the bat red (game over)
' Bytes BASIC POKEs:
'   60009 bat's top line (0-152)   60010 gap top  60011 gap end
'   60012 1 = start a new pipe     60013 1 = play, 0 = title
'   60014-60015 "HB": the code is loaded
'   60016 gravity  60017 flap speed  60018 fastest fall
'   60019 frames per step (speeds are in quarter pixels a step)
' =============================================================
' Main program. CLEAR 59999 keeps BASIC below 60000, then the
' code is loaded from tape unless it is already in memory.
CLEAR 59999
IF PEEK(60014) <> 72 OR PEEK(60015) <> 66 THEN LOAD "hbcode" CODE
RANDOMIZE
best% = 0
' the game-over box's rows, made once so no string is left over
box$ = STRING$(28, " ")
title
REPEAT
  play
  game_over
UNTIL FALSE
'
DEF PROC start
  ' The tape saves the program with AUTO start, so this runs
  ' once it has loaded. RUN begins again at the top, where the
  ' main program can use CLEAR (it must not be in a PROC).
  RUN
ENDPROC
'
DEF PROC header
  ' The score line along the top: name, score and best score.
  PRINT AT 0, 2; PAPER 1; INK 6; BRIGHT 1; "HAPPY BAT";
  PRINT AT 0, 24; PAPER 1; INK 7; BRIGHT 1; "SCORE "; score%; "   ";
  PRINT AT 0, 46; PAPER 1; INK 7; BRIGHT 1; "BEST "; best%; "   ";
ENDPROC
'
DEF PROC footer
  ' The help text on the bottom row, black on the green grass:
  ' on the title and game-over screens only (CALL 60000 clears
  ' it when a game starts).
  PRINT AT 23, 2; PAPER 4; INK 0; BRIGHT 1; "SPACE  flap"; TAB(44); "BREAK  stop";
ENDPROC
'
DEF PROC release
  ' Wait until SPACE is let go, so one press is not read twice.
  WHILE KEY(" ")
  WEND
ENDPROC
'
DEF PROC title
  ' The title screen. CALL 60000 then POKE 60013, 0 is title
  ' mode: only the ground scrolls, and BASIC bobs the bat up
  ' and down on the spot until SPACE is pressed.
  LOCAL t%, r%
  BORDER 0: PAPER 1: INK 7: BRIGHT 1: CLS
  score% = 0
  CALL 60000
  POKE 60013, 0
  header
  footer
  PRINT AT 5, 28; PAPER 8; INK 6; BRIGHT 1; "H A P P Y    B A T";
  PRINT AT 8, 26; PAPER 8; INK 7; BRIGHT 1; "Fly the bat through the gaps";
  PRINT AT 9, 26; PAPER 8; INK 7; BRIGHT 1; "in the pipes. Do not touch a";
  PRINT AT 10, 26; PAPER 8; INK 7; BRIGHT 1; "pipe, the ground or the sky!";
  PRINT AT 13, 26; PAPER 8; INK 5; BRIGHT 1; "SPACE    flap your wings";
  PRINT AT 14, 26; PAPER 8; INK 5; BRIGHT 1; "Score a point for each pipe.";
  PRINT AT 18, 28; PAPER 8; INK 6; BRIGHT 1; FLASH 1; "Press SPACE to start";
  t% = 0
  REPEAT
    t% = t% + 1
    POKE 60009, 60 + ABS(t% MOD 16 - 8)
    r% = USR 60003
  UNTIL KEY(" ")
  release
ENDPROC
'
DEF PROC play
  ' One game. The flight itself (SPACE, gravity, the top and
  ' the ground) is in the machine code, so that no press is
  ' missed; BASIC sets its constants here. Each pass of the
  ' loop is one step of 2 frames (25 a second): USR 60003
  ' moves everything 4 pixels and reports a crash or a point.
  ' BASIC starts a new pipe every n% steps: 32 (128 pixels
  ' apart) at first, closing up to 24 (96 pixels) as the score
  ' rises (see new_pipe). The bottom row is left empty in play.
  LOCAL n%, r%, g%, gap%
  POKE 60016, 2: ' gravity
  POKE 60017, 18: ' flap
  POKE 60018, 20: ' fastest fall
  POKE 60019, 2: ' frames per step
  POKE 60009, 64: ' the bat starts in the middle
  CALL 60000
  score% = 0
  header
  n% = 24: g% = 56: ' the first pipe comes after 24 steps
  REPEAT
    r% = USR 60003
    n% = n% - 1: IF n% = 0 THEN new_pipe
    IF r% = 2 THEN point
  UNTIL r% = 1
ENDPROC
'
DEF PROC new_pipe
  ' Start the next pipe. Its gap is near the last one (g% moves
  ' up to 32 lines) and keeps its caps inside the playfield.
  ' Easy at first: the gap is 78 lines at score 0 and closes 2
  ' lines a point, down to 52 from score 13. The next pipe
  ' comes 32 steps later at first, one step sooner every 2
  ' points, down to 24 steps from score 16.
  gap% = MAX(52, 78 - 2 * score%)
  n% = MAX(24, 32 - (score% >> 1))
  g% = g% + 8 * RND(9) - 40
  g% = MAX(16, MIN(g%, 144 - gap%))
  POKE 60010, g%
  POKE 60011, g% + gap%
  POKE 60012, 1
ENDPROC
'
DEF PROC point
  ' The bat got past a pipe: one more point.
  score% = score% + 1
  PRINT AT 0, 30; PAPER 1; INK 7; BRIGHT 1; score%;
  BEEP 0.01, 48
ENDPROC
'
DEF PROC game_over
  ' The bat turns red and a falling tune plays. A new best score
  ' is kept in best%, which lasts until the program is run
  ' again. Then SPACE starts the next game.
  LOCAL n%, r%
  CALL 60006
  FOR n% = 0 TO 4
    BEEP 0.06, 12 - n% * 5
  NEXT
  FOR r% = 7 TO 14
    PRINT AT r%, 24; PAPER 2; INK 7; BRIGHT 1; box$;
  NEXT
  PRINT AT 8, 29; PAPER 2; INK 6; BRIGHT 1; "G A M E    O V E R";
  PRINT AT 10, 31; PAPER 2; INK 7; BRIGHT 1; "Score  "; score%;
  IF score% > best%
    best% = score%
    PRINT AT 11, 31; PAPER 2; INK 6; BRIGHT 1; FLASH 1; "A new best!";
  ELSE
    PRINT AT 11, 31; PAPER 2; INK 7; BRIGHT 1; "Best   "; best%;
  ENDIF
  PRINT AT 13, 27; PAPER 2; INK 5; BRIGHT 1; "SPACE to fly again";
  header
  footer
  WAIT 40
  release
  REPEAT
    WAIT 1
  UNTIL KEY(" ")
ENDPROC
```

## happybat.asm

```asm
; =============================================================================
; happybat.asm - the machine-code half of Happy Bat, for OpticOS v1.0.1
; Assemble with pasmo:   pasmo --bin happybat.asm hbcode.bin
;
; Written from scratch for OpticOS (clean room): no Sinclair ROM code is used
; or called.  The code touches only the screen, the keyboard/speaker port and
; its own variables, and reads the frame counter FRAMES (23672), whose
; address OpticOS keeps.  It does not use IX, IY or the alternate registers,
; so the OpticBASIC interpreter's state is left alone.  It needs interrupts on
; (they are, under OpticBASIC) because it waits for frames with HALT.
;
; OpticBASIC's CALL and USR take no register arguments, so BASIC POKEs the
; parameter block below, and USR 60003 hands back the result of a step in BC.
;
; Screen layout (pixel lines from the top of the screen):
;   lines   0- 15  character rows 0-1: the score line, printed by BASIC
;   lines  16-175  the playfield, 160 lines: sky, pipes and the bat
;   lines 176-183  character row 22: the ground, which scrolls
;   lines 184-191  character row 23: help text, printed by BASIC
; Horizontal positions are counted in nibbles (4 pixels = one character at
; 64 columns): the screen is 64 nibbles wide and everything moves one nibble
; left per step.
; =============================================================================

PF_TOP   equ 16             ; first screen line of the playfield
PF_H     equ 160            ; playfield height in lines
GR_TOP   equ 176            ; first line of the ground
SC_END   equ 184            ; one past the ground's last line
YMAX     equ 152            ; lowest top line for the 8-line bat
BAT_COL  equ 8              ; the bat's byte column: x = 64-79
BAT_NIB  equ 16             ; ... = nibble 16
NPIPE    equ 4              ; pipe slots (pipes 24 nibbles apart: at most 4)
FREE     equ $80            ; x value marking a free slot
A_SKY    equ $4C            ; bright, blue paper, green ink (pipes)
A_BAT    equ $4E            ; bright, blue paper, yellow ink (the bat)
A_DEAD   equ $4A            ; bright, blue paper, red ink (a dead bat)
A_GROUND equ $66            ; bright, green paper, yellow ink
A_BASE   equ $60            ; bright, green paper, black ink (row 23)
ATTRS    equ $5800          ; start of the attribute map
FRAMES   equ 23672          ; OpticOS frame counter (low byte)

        org 60000

; ---- entry points: the addresses BASIC calls ---------------------------------
        jp init             ; 60000  CALL 60000: new playfield
        jp step             ; 60003  USR 60003: one step -> BC = 0, 1 or 2
        jp dead             ; 60006  CALL 60006: colour the bat red

; ---- parameters, POKEd (and PEEKed) by BASIC -------------------------------
baty:   defb 72             ; 60009  bat's top line in the playfield (0-152);
                            ;        BASIC sets it on the title screen and
                            ;        before CALL 60000; in play the code moves it
gaptop: defb 40             ; 60010  first line of the next pipe's gap
gapbot: defb 88             ; 60011  first line below that gap
newpipe: defb 0             ; 60012  POKE 1: start that pipe at the right edge
mode:   defb 1              ; 60013  1 = play; 0 = title (no gravity, no
                            ;        pipes: only the ground scrolls)
sig:    defm "HB"           ; 60014  signature: BASIC checks it to see
                            ;        whether the code is already loaded
grav:   defb 2              ; 60016  gravity, quarter pixels per step per step
flapv:  defb 18             ; 60017  a flap's upward speed, quarter px / step
vmax:   defb 20             ; 60018  fastest fall, quarter pixels per step
pacev:  defb 2              ; 60019  frames per step at least (1 or more)

; ---- internal state -------------------------------------------------------
y16:    defw 288            ; bat height in quarter pixels (0 - 4*YMAX)
v16:    defw 0              ; its speed, quarter pixels per step (+ = down)
pkey:   defb 0              ; 1 if SPACE was down at the last step
oldy:   defb 0              ; where the bat was drawn last
oldspr: defw spr_up         ; and with which wing frame
drawn:  defb 0              ; 1 while the bat is on the screen
tick:   defb 0              ; step counter, for the wing beat
phase:  defb 0              ; ground pattern phase, 0-3
lastf:  defb 0              ; FRAMES at the last step, for pacing
crash:  defb 0              ; set during a step: hit the top or the ground
scored: defb 0              ; set during a step: a pipe got past the bat
ptab:   defs NPIPE*4,FREE   ; pipes: x (nibble of the left edge), gap top,
                            ;        gap bottom, spare
pg1:    defb 0              ; the pipe being drawn: its gap top
pg2:    defb 0              ;   and gap bottom
scol:   defb 0              ;   first byte column written on each line
slen:   defw 0              ;   bytes written on each line (high byte 0)
sbody:  defw 0              ;   where in its body pattern to start
scap:   defw 0              ;   and in its cap pattern
sptr:   defw 0              ; pattern for the lines seg is drawing

; -----------------------------------------------------------------------------
; init: clear the screen below the score line, colour the sky, ground and
; help row, draw the ground, and reset everything: no pipes, no bat on the
; screen, play mode, the bat at height baty and not moving.
; -----------------------------------------------------------------------------
init:   ld c,PF_TOP         ; C = screen line
in_clr: ld a,c
        call ln_addr        ; HL = start of line C
        ld b,32
        xor a
in_cb:  ld (hl),a           ; clear its 32 bytes
        inc l
        djnz in_cb
        inc c
        ld a,c
        cp 192
        jr nz,in_clr
        ld hl,ATTRS+2*32    ; rows 2-21: sky
        ld bc,20*32
        ld a,A_SKY
        call fill
        ld hl,ATTRS+22*32   ; row 22: ground
        ld bc,32
        ld a,A_GROUND
        call fill
        ld hl,ATTRS+23*32   ; row 23: help text
        ld bc,32
        ld a,A_BASE
        call fill
        ld de,ginit         ; draw the ground: two bytes, 16 times a line
        ld c,GR_TOP
in_gr:  ld a,c
        call ln_addr
        ld b,16
in_g2:  ld a,(de)
        ld (hl),a
        inc l
        inc de
        ld a,(de)
        ld (hl),a
        inc l
        dec de
        djnz in_g2
        inc de              ; next ground line's pair
        inc de
        inc c
        ld a,c
        cp SC_END
        jr nz,in_gr
        ld hl,ptab          ; every pipe slot free
        ld bc,NPIPE*4
        ld a,FREE
        call fill
        xor a
        ld (drawn),a        ; no bat on the screen
        ld (tick),a
        ld (phase),a        ; 64 nibbles drawn: the next one is phase 0
        ld (newpipe),a
        ld h,a
        ld l,a
        ld (v16),hl         ; not moving
        inc a
        ld (mode),a         ; play mode
        ld (pkey),a         ; a SPACE still held from before is not a flap
        ld a,(baty)         ; height in quarter pixels = baty * 4
        ld l,a
        add hl,hl
        add hl,hl
        ld (y16),hl
        ld a,(FRAMES)
        ld (lastf),a
        ret

; -----------------------------------------------------------------------------
; step: one step of the game, called with h% = USR 60003.
;  1. wait until pacev frames have passed since the last step, so the game
;     runs at the same speed however much is on the screen;
;  2. take the bat off the screen;
;  3. in play: read SPACE and move the bat (phys), then start, move and draw
;     the pipes (pipes);
;  4. scroll the ground; put the bat back, testing its pixels as it goes.
; Returns BC = 1 if the bat crashed (pipe, ground or top), else 2 if a pipe
; has just got past the bat (a point), else 0.
; -----------------------------------------------------------------------------
step:   call pace
        call bat_off
        xor a
        ld (crash),a
        ld (scored),a
        ld a,(mode)
        or a
        jr z,st_t           ; title: no gravity, no pipes
        call phys
        call pipes
st_t:   call ground
        ld hl,tick
        inc (hl)
        call bat_on         ; C <> 0: the bat touched a pipe
        ld a,c
        or a
        jr z,st_1
        ld (crash),a
st_1:   ld bc,1
        ld a,(crash)
        or a
        ret nz              ; 1: crashed
        inc c
        ld a,(scored)
        or a
        ret nz              ; 2: scored
        ld c,0
        ret                 ; 0: flying on

; -----------------------------------------------------------------------------
; pace: HALT until at least pacev frames have passed since the last call.
; -----------------------------------------------------------------------------
pace:   ld hl,lastf
pa_lp:  ld a,(FRAMES)
        sub (hl)            ; frames since the last step
        ld b,a
        ld a,(pacev)
        dec a
        cp b                ; carry if B >= pacev
        jr c,pa_ok
        halt                ; wait for the next frame
        jr pa_lp
pa_ok:  ld a,(FRAMES)
        ld (hl),a
        ret

; -----------------------------------------------------------------------------
; phys: the bat's flight.  A new press of SPACE (it was up at the last step)
; sets the speed to -flapv and chirps; then gravity adds grav to the speed, up
; to vmax downwards, and the speed is added to the height.  Going above the
; top or below YMAX stops the bat there and sets crash.  baty = height / 4.
; -----------------------------------------------------------------------------
phys:   ld a,$7F            ; keyboard half-row SPACE, SYMBOL, M, N, B
        in a,($FE)
        cpl
        and 1               ; A = 1 while SPACE is held
        ld hl,pkey
        ld b,(hl)
        ld (hl),a
        jr z,ph_g           ; not held
        dec b
        jr z,ph_g           ; held, but it was held last step too
        ld a,(flapv)        ; a flap: speed = -flapv
        neg
        ld l,a
        ld h,$FF
        ld (v16),hl
        call chirp
ph_g:   ld hl,(v16)         ; gravity
        ld a,(grav)
        ld e,a
        ld d,0
        add hl,de
        bit 7,h
        jr nz,ph_v          ; still going up: no limit
        ld a,(vmax)
        ld e,a
        ld a,h
        or a
        jr nz,ph_cl
        ld a,l
        cp e
        jr c,ph_v
ph_cl:  ex de,hl            ; falling too fast: speed = vmax
ph_v:   ld (v16),hl
        ld de,(y16)
        add hl,de           ; new height
        bit 7,h
        jr z,ph_lo
        ld hl,0             ; above the top of the playfield
        jr ph_cr
ph_lo:  push hl
        ld de,YMAX*4+1
        or a
        sbc hl,de
        pop hl
        jr c,ph_ok
        ld hl,YMAX*4        ; on the ground
ph_cr:  ld a,1
        ld (crash),a
ph_ok:  ld (y16),hl
        srl h               ; baty = height / 4
        rr l
        srl h
        rr l
        ld a,l
        ld (baty),a
        ret

; -----------------------------------------------------------------------------
; chirp: a short rising click on the speaker for a flap (about 1 ms).
; Bit 4 of port 254 drives the speaker; bits 0-2 keep the border black.
; -----------------------------------------------------------------------------
chirp:  ld b,24
ch_lp:  ld a,b
        and 1
        rlca
        rlca
        rlca
        rlca
        out ($FE),a
        ld a,b
        add a,8
ch_d:   dec a
        jr nz,ch_d
        djnz ch_lp
        ret

; -----------------------------------------------------------------------------
; pipes: if BASIC asked for one (newpipe), put a new pipe in a free slot at
; x = 64, just off the right edge, with the gap from gaptop/gapbot.  Then
; move and redraw every pipe in use (pipe1).
; -----------------------------------------------------------------------------
pipes:  ld a,(newpipe)
        or a
        jr z,pp_mv
        xor a
        ld (newpipe),a
        ld hl,ptab
        ld de,4
        ld b,NPIPE
pp_f:   ld a,(hl)
        cp FREE
        jr z,pp_new
        add hl,de
        djnz pp_f
        jr pp_mv            ; no free slot (cannot happen 24 steps apart)
pp_new: ld (hl),64
        inc hl
        ld a,(gaptop)
        ld (hl),a
        inc hl
        ld a,(gapbot)
        ld (hl),a
pp_mv:  ld hl,ptab
        ld b,NPIPE
pp_lp:  push bc
        push hl
        call pipe1
        pop hl
        ld de,4
        add hl,de
        pop bc
        djnz pp_lp
        ret

; -----------------------------------------------------------------------------
; pipe1: move the pipe in slot HL one nibble left and draw it.  A pipe is 8
; nibbles wide: x .. x+7.  Its right edge passing the bat (x = 8, so x+7 = 15
; is just left of nibble 16) sets scored.  A pipe gone off the left (x < -8)
; frees its slot.  Each line gets 5 bytes from a pattern (body or cap, for
; even or odd x), clipped to the screen; the 5th byte rubs out the pixels
; the pipe has just left on its right.  The gap's lines are not touched.
; -----------------------------------------------------------------------------
pipe1:  ld a,(hl)
        cp FREE
        ret z
        dec a               ; one nibble left
        ld (hl),a
        cp BAT_NIB-8
        jr nz,p1_a
        ld a,1
        ld (scored),a       ; its right edge is past the bat
        ld a,(hl)
p1_a:   add a,8             ; x from -8 to 64 is on (or next to) the screen
        cp 73
        jr c,p1_on
        ld (hl),FREE        ; gone: free the slot
        ret
p1_on:  inc hl
        ld a,(hl)
        ld (pg1),a          ; gap top
        inc hl
        ld a,(hl)
        ld (pg2),a          ; gap bottom
        dec hl
        dec hl
        ld a,(hl)           ; A = x
        ld de,body_e        ; patterns for even x
        ld bc,cap_e
        bit 0,a
        jr z,p1_ev
        ld de,body_o        ; or odd x
        ld bc,cap_o
p1_ev:  ld (sbody),de
        ld (scap),bc
        sra a               ; A = first byte column = x / 2, rounded down
        ld c,5              ; C = bytes a line
        bit 7,a
        jr z,p1_r
        neg                 ; partly off the left: A = bytes cut off
        ld b,a
        ld a,c
        sub b
        ld c,a
        ld e,b              ; start that far into the patterns
        ld d,0
        ld hl,(sbody)
        add hl,de
        ld (sbody),hl
        ld hl,(scap)
        add hl,de
        ld (scap),hl
        xor a               ; and at column 0
p1_r:   ld (scol),a
        add a,c             ; partly off the right?
        sub 32
        jr c,p1_w
        ld b,a              ; B = bytes beyond column 31
        ld a,c
        sub b
        ret z               ; nothing on the screen yet
        ret c
        ld c,a
p1_w:   ld a,c
        ld (slen),a
        ld hl,(sbody)       ; body from the top down to the top cap
        ld (sptr),hl
        ld a,(pg1)
        sub 4
        ld b,a
        xor a
        call seg
        ld hl,(scap)        ; the cap above the gap
        ld (sptr),hl
        ld a,(pg1)
        sub 4
        ld b,4
        call seg
        ld a,(pg2)          ; the cap below it
        ld b,4
        call seg
        ld hl,(sbody)       ; body from below that cap to the ground
        ld (sptr),hl
        ld a,(pg2)
        add a,4
        ld c,a
        ld a,PF_H
        sub c
        ld b,a
        ld a,c
        jp seg

; -----------------------------------------------------------------------------
; seg: draw B lines (B > 0) of a pipe, from playfield line A down: on each
; line copy slen bytes of the pattern at sptr to byte column scol.
; -----------------------------------------------------------------------------
seg:    add a,PF_TOP
        call ln_addr
        ld a,(scol)
        or l
        ld l,a              ; HL = first byte to write
sg_lp:  push bc
        push hl
        ex de,hl            ; DE = screen
        ld hl,(sptr)
        ld bc,(slen)
        ldir
        pop hl
        call nxt_line
        pop bc
        djnz sg_lp
        ret

; -----------------------------------------------------------------------------
; ground: scroll the 8 ground lines 4 pixels left, feeding in each line's
; next pattern nibble at the right, then advance the pattern phase.
; -----------------------------------------------------------------------------
ground: ld a,(phase)
        ld e,a
        ld d,0
        ld hl,gpat
        add hl,de
        ex de,hl            ; DE -> this phase's nibble for ground line 0
        ld c,GR_TOP
gd_lp:  ld a,c
        call ln_addr
        ld a,l
        or 31               ; the line's last byte
        ld l,a
        ld a,(de)           ; nibble to feed in
        call rot_line
        inc de              ; same phase, next line: 4 bytes on
        inc de
        inc de
        inc de
        inc c
        ld a,c
        cp SC_END
        jr nz,gd_lp
        ld a,(phase)
        inc a
        and 3
        ld (phase),a
        ret

; -----------------------------------------------------------------------------
; rot_line: scroll one screen line 4 pixels left.  HL = its last byte (x 31),
; A's low nibble = the 4 pixels to bring in at the right.  RLD moves the
; byte's low nibble up, A's nibble into the low half, and the byte's old high
; nibble into A, which carries on into the byte to its left.  Unrolled:
; 32 x (RLD, DEC L), about 700 T-states a line.
; -----------------------------------------------------------------------------
rot_line:
        rept 31
        rld
        dec l
        endm
        rld
        ret

; -----------------------------------------------------------------------------
; bat_on: draw the bat at baty with this step's wing frame (the wings beat
; every two steps) and colour its cells yellow.  Returns C <> 0 if any of its
; pixels landed on something already on the screen (a pipe).
; -----------------------------------------------------------------------------
bat_on: ld a,(tick)
        and 2
        ld hl,spr_up
        jr z,bo_1
        ld hl,spr_dn
bo_1:   ld (oldspr),hl
        ex de,hl            ; DE = sprite
        ld a,(baty)
        ld (oldy),a
        call bat_xor        ; C = sprite AND screen, before drawing
        push bc
        ld a,(oldy)
        ld e,A_BAT
        call bat_attr
        ld a,1
        ld (drawn),a
        pop bc
        ret

; -----------------------------------------------------------------------------
; bat_off: if the bat is on the screen, XOR it away (which restores exactly
; what was under it) and give its cells back the sky colour.
; -----------------------------------------------------------------------------
bat_off: ld a,(drawn)
        or a
        ret z
        xor a
        ld (drawn),a
        ld de,(oldspr)
        ld a,(oldy)
        call bat_xor
        ld a,(oldy)
        ld e,A_SKY
        jp bat_attr

; -----------------------------------------------------------------------------
; dead: colour the bat red where it was last drawn (game over).
; -----------------------------------------------------------------------------
dead:   ld a,(oldy)
        ld e,A_DEAD
        jp bat_attr

; -----------------------------------------------------------------------------
; bat_xor: XOR the 16 x 8 sprite at DE onto the screen at byte column BAT_COL,
; playfield line A.  Returns C = the OR of (sprite AND screen) taken before
; each byte is changed: non-zero means the bat overlapped something.
; -----------------------------------------------------------------------------
bat_xor: add a,PF_TOP       ; playfield line -> screen line
        ld b,8
        ld c,0
bx_lp:  push af
        call ln_addr
        ld a,l
        or BAT_COL
        ld l,a
        ld a,(de)           ; left byte
        and (hl)
        or c
        ld c,a
        ld a,(de)
        xor (hl)
        ld (hl),a
        inc de
        inc l
        ld a,(de)           ; right byte
        and (hl)
        or c
        ld c,a
        ld a,(de)
        xor (hl)
        ld (hl),a
        inc de
        pop af
        inc a
        djnz bx_lp
        ret

; -----------------------------------------------------------------------------
; bat_attr: set the attribute E in the cells the bat covers when its top is at
; playfield line A: two columns, in the character row of its top line and of
; its bottom line (the same row when it is aligned).
; -----------------------------------------------------------------------------
bat_attr:
        add a,PF_TOP
        push af
        call ba_row         ; row of the top line
        pop af
        add a,7             ; row of the bottom line
ba_row: and $F8             ; A = screen line: row * 8
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl           ; row * 32
        ld a,h
        add a,ATTRS/256
        ld h,a
        ld a,l
        or BAT_COL
        ld l,a
        ld (hl),e
        inc l
        ld (hl),e
        ret

; -----------------------------------------------------------------------------
; ln_addr: A = screen line 0-191 -> HL = address of its first byte.
; The Spectrum interleaves its screen: the address bits are
;   0 1 0 y7 y6 y2 y1 y0 | y5 y4 y3 x4 x3 x2 x1 x0
; Uses A and HL only, so BC and DE survive.
; -----------------------------------------------------------------------------
ln_addr:
        ld l,a
        and 7               ; y2-y0
        or $40
        ld h,a
        ld a,l
        rra
        rra
        rra
        and $18             ; y7 y6 -> bits 4, 3
        or h
        ld h,a
        ld a,l
        rla
        rla
        and $E0             ; y5-y3 -> bits 7-5
        ld l,a
        ret

; -----------------------------------------------------------------------------
; nxt_line: HL = a screen address -> the same column one line down.  Within
; a character row that is the next 256 bytes; at a row boundary, 32 bytes on
; and back 8 x 256 (unless that crosses into the next third of the screen).
; -----------------------------------------------------------------------------
nxt_line:
        inc h
        ld a,h
        and 7
        ret nz
        ld a,l
        add a,32
        ld l,a
        ret c
        ld a,h
        sub 8
        ld h,a
        ret

; -----------------------------------------------------------------------------
; fill: store A in BC bytes from HL (BC > 0), using LDIR.
; -----------------------------------------------------------------------------
fill:   ld (hl),a
        dec bc
        ld a,b
        or c
        ret z
        ld d,h
        ld e,l
        inc de
        ldir
        ret

; ---- data -------------------------------------------------------------------
; Sprites, ground and pipe patterns (generated by tools/gen_tables.py; the
; comments show the pixels).
spr_up:                         ; wings up: 16 x 8 pixels, 2 bytes a line
        defb $04,$20          ;      #    #     
        defb $87,$E1          ; #    ######    #
        defb $C5,$A3          ; ##   # ## #   ##
        defb $EF,$F7          ; ### ######## ###
        defb $7D,$BE          ;  ##### ## ##### 
        defb $3E,$7C          ;   #####  #####  
        defb $0F,$F0          ;     ########    
        defb $02,$40          ;       #  #      
spr_dn:                         ; wings down
        defb $04,$20          ;      #    #     
        defb $07,$E0          ;      ######     
        defb $05,$A0          ;      # ## #     
        defb $7F,$FE          ;  ############## 
        defb $FF,$FF          ; ################
        defb $ED,$B7          ; ### ## ## ## ###
        defb $CE,$73          ; ##  ###  ###  ##
        defb $83,$C1          ; #     ####     #
gpat:                           ; ground: 8 lines x 4 nibbles (one 16-pixel repeat)
        defb $F,$F,$F,$F      ; ################
        defb $8,$3,$8,$3      ; #     ###     ##
        defb $0,$E,$0,$E      ;     ###     ### 
        defb $3,$8,$3,$8      ;   ###     ###   
        defb $E,$0,$E,$0      ; ###     ###     
        defb $8,$3,$8,$3      ; #     ###     ##
        defb $0,$E,$0,$E      ;     ###     ### 
        defb $8,$8,$8,$8      ; #   #   #   #   
ginit:                          ; the same pattern as whole bytes, for the first fill
        defb $FF,$FF
        defb $83,$83
        defb $0E,$0E
        defb $38,$38
        defb $E0,$E0
        defb $83,$83
        defb $0E,$0E
        defb $88,$88
body_e:  defb $0F,$BF,$FF,$E0,$00   ; |    ##### #################             |  x even
body_o:  defb $00,$FB,$FF,$FE,$00   ; |        ##### #################         |  x odd
cap_e:  defb $7F,$BF,$FF,$FE,$00   ; | ######## #####################         |  x even
cap_o:  defb $07,$FB,$FF,$FF,$E0   ; |     ######## #####################     |  x odd

code_end:
```
