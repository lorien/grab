#!/bin/sh
cd docs
make html
cd -
rsync -az --progress /web/grab/docs/_build/html web@frodo:/web/grablib/docs
