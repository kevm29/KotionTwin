import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from abcdump import ABC
def body_positions(data):
    return ABC(data).body_pos
