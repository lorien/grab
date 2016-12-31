from setuptools import setup, find_packages
import os

ROOT = os.path.dirname(os.path.realpath(__file__))

setup(
    name='grab',
    version='0.6.32',
    description='Web Scraping Framework',
    long_description=open(os.path.join(ROOT, 'README.rst')).read(),
    url='http://grablib.org',
    author='Gregory Petukhov',
    author_email='lorien@lorien.name',

    packages=find_packages(exclude=['test', 'test.files']),
    install_requires=['lxml', 'pycurl', 'selection', 'weblib>=0.1.10', 'six',
                      'user_agent'],

    license='MIT',
    keywords='pycurl multicurl curl network parsing grabbing scraping'
             ' lxml xpath data mining',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
