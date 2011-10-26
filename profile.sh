#!/bin/sh
# To run this tool you'll need:
# * aptitude install python-profiler kcachegrind
# * pip install  pyprof2calltree
python -m cProfile -o prof speed.py
pyprof2calltree -i prof -k
