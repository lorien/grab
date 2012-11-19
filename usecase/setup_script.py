import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

os.chdir(ROOT)
sys.path.insert(0, ROOT)
