#!/bin/sh
hg push
python setup.py register sdist upload
