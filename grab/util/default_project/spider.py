#!/usr/bin/env python
# coding: utf-8
from grab.spider import Spider, Task
from grab.tools.logs import default_logging
from grab import Grab
import logging
from urlparse import urlsplit, parse_qs, parse_qsl, urlunsplit, urljoin
from grab.tools.lxml_tools import parse_html, render_html, drop_node, clone_node
import traceback
import urllib
from collections import defaultdict
import re

from database import db

class {{ PROJECT_NAME_CAMELCASE }}Spider(Spider):
    initial_urls = ['']

    def task_initial(self, grab, task):
        pass
