#!/bin/sh
# To run this tool you'll need:
# * aptitude install python-profiler kcachegrind
# * pip install  pyprof2calltree
python -m cProfile -o prof $1
pyprof2calltree -i prof -k
