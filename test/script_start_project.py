from grab.spider import Spider, Task
from grab.script import crawl
from grab.util.module import SPIDER_REGISTRY
from unittest import TestCase
import os
import subprocess
from grab.script import start_project
from grab.error import GrabError
from weblib.files import clear_directory
from argparse import ArgumentParser

from test.util import TMP_DIR


class ScriptStartProjectTestCase(TestCase):
    def test_start_project(self):
        old_dir = os.getcwd()
        os.chdir(TMP_DIR)
        dir_ = os.path.join(TMP_DIR, 'test_project')
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
        clear_directory(dir_)
        os.rmdir(dir_)

    def test_directory_already_exists(self):
        old_dir = os.getcwd()
        os.chdir(TMP_DIR)
        dir_ = os.path.join(TMP_DIR, 'test_project')
        os.mkdir(dir_)
        self.assertRaises(GrabError, start_project.main,
                          project_name='test_project', template=None)

        os.chdir(old_dir)
        os.rmdir(dir_)

    def test_explicit_template_name(self):
        old_dir = os.getcwd()
        os.chdir(TMP_DIR)
        test_dir = os.path.dirname(__file__)
        project_sample_path = os.path.join(test_dir, 'files/project_sample')
        start_project.main(project_name='test_project',
                           template=project_sample_path)
        self.assertTrue(os.path.join(TMP_DIR, 'test_project/foo.py'))
        os.chdir(old_dir)

        dir_ = os.path.join(TMP_DIR, 'test_project')
        clear_directory(dir_)
        os.rmdir(dir_)

    def test_normalize_extension(self):
        self.assertEqual('foo/bar.py',
                         start_project.normalize_extension('foo/bar.py'))
        self.assertEqual('foo/bar.py',
                         start_project.normalize_extension('foo/bar._py'))

    def test_setup_arg_parser(self):
        parser = ArgumentParser()
        start_project.setup_arg_parser(parser)
        opts = parser.parse_args(['foo'])
        self.assertTrue('project_name' in opts)
        self.assertTrue('template' in opts)
