"""Shared helpers for running Happy Bat in real Fuse (fuse-sdl, 48K, the
OpticOS v1.0.1 release ROM) on a private Xvfb display."""
import os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROM, TAPE, HB
from fuse_phase1 import Fuse, ENV, x
from PIL import ImageGrab
def kill(): subprocess.run(['pkill', '-f', 'fuse-sdl'])
def grab(f):
    X, Y, W, H = f.geo
    return ImageGrab.grab(bbox=(X, Y, X + W, Y + H), xdisplay=':57').convert('RGB')
def load(f, traps, hold=0.12):
    """type LOAD "" and ENTER (Symbol Shift = Control_L); with traps off, start the tape (F8)"""
    for k in 'load': f.key(k, hold)
    f.key('space', hold); f.key('p', hold, mods=('Control_L',)); f.key('p', hold, mods=('Control_L',))
    f.key('Return', hold); time.sleep(0.3)
    if not traps: f.key('F8')
def down(k='space'): x('xdotool', 'keydown', k)
def up(k='space'): x('xdotool', 'keyup', k)
