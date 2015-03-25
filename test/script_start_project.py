from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY
from unittest import TestCase
import os
import subprocess
from grab.script import start_project

from test.util import TMP_DIR


class ScriptStartProjectTestCase(TestCase):
    def test_start_project(self):
        old_dir = os.getcwd()
        os.chdir(TMP_DIR)
        start_project.main(project_name='test_project', template=None)
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
