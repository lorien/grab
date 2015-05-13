from __future__ import absolute_import
from weblib.__init__ import *  # noqa
from grab.tools.hook import CustomImporter
import sys

sys.meta_path.append(CustomImporter())
