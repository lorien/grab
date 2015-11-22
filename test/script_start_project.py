from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY
from unittest import TestCase
import os
import subprocess
from grab.script import start_project
from grab.error import GrabError
from argparse import ArgumentParser

from test.util import temp_dir


class ScriptStartProjectTestCase(TestCase):
    def test_start_project(self):
        with temp_dir() as tmp_dir:
            old_dir = os.getcwd()
            os.chdir(tmp_dir)
            dir_ = os.path.join(tmp_dir, 'test_project')
            start_project.main(project_name='test_project', template=None)
            os.chdir(old_dir)
            self.assertTrue(os.path.exists(os.path.join(dir_,
                                                        'var')))
            self.assertTrue(os.path.exists(os.path.join(dir_,
                                                        'var/log')))
            self.assertTrue(os.path.exists(os.path.join(dir_,
                                                        'var/run')))
            path = os.path.join(dir_, 'spider.py')
            self.assertTrue(
                'TestProjectSpider' in open(path).read())

    def test_directory_already_exists(self):
        with temp_dir() as tmp_dir:
            old_dir = os.getcwd()
            os.chdir(tmp_dir)
            dir_ = os.path.join(tmp_dir, 'test_project')
            os.mkdir(dir_)
            self.assertRaises(GrabError, start_project.main,
                              project_name='test_project', template=None)
            os.chdir(old_dir)

    def test_explicit_template_name(self):
        with temp_dir() as tmp_dir:
            old_dir = os.getcwd()
            os.chdir(tmp_dir)
            test_dir = os.path.dirname(__file__)
            project_sample_path = os.path.join(test_dir, 'files/project_sample')
            start_project.main(project_name='test_project',
                               template=project_sample_path)
            self.assertTrue(os.path.join(tmp_dir, 'test_project/foo.py'))
            os.chdir(old_dir)

    def test_setup_arg_parser(self):
        parser = ArgumentParser()
        start_project.setup_arg_parser(parser)
        opts = parser.parse_args(['foo'])
        self.assertTrue('project_name' in opts)
        self.assertTrue('template' in opts)
