#!/bin/sh
curl -X POST http://readthedocs.org/build/1401
sleep 30
ssh web@frodo 'cd /web/docs_grablib; ./update.sh'
