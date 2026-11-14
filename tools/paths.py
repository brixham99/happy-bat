"""Where things are.  HB is this repository (the folder above tools/).
The tests and the tape builder use the OpticOS repository's Z80 test rig
and Fuse helpers, and the OpticOS v1.0.1 ROM; neither is included here.
  OPTICOS_REPO  a checkout of https://github.com/brixham99/OpticOS
                (default: a folder OpticOS next to this repository); its
                rig runs the ROM at build/opticos.rom in that checkout
  OPTICOS_ROM   the v1.0.1 ROM file for Fuse (default: OPTICOS_REPO/build/opticos.rom)"""
import os, sys
HB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTICOS = os.environ.get('OPTICOS_REPO', os.path.join(os.path.dirname(HB), 'OpticOS'))
RIG = os.path.join(OPTICOS, 'tools', 'rig')
ROM = os.path.abspath(os.environ.get('OPTICOS_ROM', os.path.join(OPTICOS, 'build', 'opticos.rom')))
TAPE = os.path.join(HB, 'happybat.tap')
for _p in (os.path.join(OPTICOS, 'tools'), RIG, os.path.join(HB, 'tools')):
    if _p not in sys.path: sys.path.insert(0, _p)
