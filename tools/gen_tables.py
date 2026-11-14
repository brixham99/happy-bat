# Generates the sprite and ground tables for happybat.asm from ASCII art.
UP = [".....X....X.....",
      "X....XXXXXX....X",
      "XX...X.XX.X...XX",
      "XXX.XXXXXXXX.XXX",
      ".XXXXX.XX.XXXXX.",
      "..XXXXX..XXXXX..",
      "....XXXXXXXX....",
      "......X..X......"]
DN = [".....X....X.....",
      ".....XXXXXX.....",
      ".....X.XX.X.....",
      ".XXXXXXXXXXXXXX.",
      "XXXXXXXXXXXXXXXX",
      "XXX.XX.XX.XX.XXX",
      "XX..XXX..XXX..XX",
      "X.....XXXX.....X"]
def spr(name, art, note):
    print('%s:                         ; %s' % (name, note))
    for r in art:
        v = int(r.replace('X', '1').replace('.', '0'), 2)
        print('        defb $%02X,$%02X          ; %s' % (v >> 8, v & 255, r.replace('.', ' ').replace('X', '#')))
spr('spr_up', UP, 'wings up: 16 x 8 pixels, 2 bytes a line')
spr('spr_dn', DN, 'wings down')
# ground: 8 lines; each has a 16-pixel pattern = 4 nibbles (phases 0-3)
G = []
for r in range(8):
    if r == 0: px = [1] * 16
    elif r == 7: px = [1 if x % 4 == 0 else 0 for x in range(16)]
    else: px = [1 if (x + 2 * r) % 8 < 3 else 0 for x in range(16)]
    G.append(px)
print('gpat:                           ; ground: 8 lines x 4 nibbles (one 16-pixel repeat)')
for r, px in enumerate(G):
    nib = [int(''.join(map(str, px[4 * p:4 * p + 4])), 2) for p in range(4)]
    print('        defb %s      ; %s' % (','.join('$%X' % n for n in nib), ''.join('#' if p else ' ' for p in px)))
print('ginit:                          ; the same pattern as whole bytes, for the first fill')
for r, px in enumerate(G):
    b = [int(''.join(map(str, px[8 * i:8 * i + 8])), 2) for i in range(2)]
    print('        defb $%02X,$%02X' % tuple(b))
# pipe span patterns: 5 bytes written on each line of a pipe.  The pipe is 8
# nibbles wide (x .. x+7); even x starts at a byte, odd x in its low nibble.
BODY = [0x0, 0xF, 0xB, 0xF, 0xF, 0xF, 0xE, 0x0]
CAP  = [0x7, 0xF, 0xB, 0xF, 0xF, 0xF, 0xF, 0xE]
def span(nibs):
    return [nibs[2 * i] << 4 | nibs[2 * i + 1] for i in range(5)]
def pic(bs): return ''.join(format(b, '08b') for b in bs).replace('0', ' ').replace('1', '#')
for name, k in (('body', BODY), ('cap', CAP)):
    e = span(k + [0, 0]); o = span([0] + k + [0])
    print('%s_e:  defb %s   ; |%s|  x even' % (name, ','.join('$%02X' % b for b in e), pic(e)))
    print('%s_o:  defb %s   ; |%s|  x odd' % (name, ','.join('$%02X' % b for b in o), pic(o)))
