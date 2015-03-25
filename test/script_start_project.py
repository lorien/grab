from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY
from unittest import TestCase
import os
import subprocess

from test.util import TMP_DIR


class ScriptStartProjectTestCase(TestCase):
    def test_crawl(self):
        old_dir = os.getcwd()
        os.chdir(TMP_DIR)
        subprocess.call(['run', 'start_project', 'test_project'])
        os.chdir(old_dir)
        self.assertTrue(os.path.exists(os.path.join(TMP_DIR,
                                                    'test_project/var')))
        self.assertTrue(os.path.exists(os.path.join(TMP_DIR,
                                                    'test_project/var/log')))
        self.assertTrue(os.path.exists(os.path.join(TMP_DIR,
                                                    'test_project/var/run')))
        path = os.path.join(TMP_DIR, 'test_project/spider.py')
        self.assertTrue(
            'TestProjectSpider' in open(path).read())
