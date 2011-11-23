from setuptools import setup, find_packages
import re

version = __import__('grab').__version__

setup(
    name = 'grab',
    version = version,
    description = 'Pycurl wrapper',
    url = 'http://bitbucket.org/lorien/grab/',
    author = 'Grigoriy Petukhov',
    author_email = 'lorien@lorien.name',

    packages = find_packages(),
    include_package_data = True,

    license = "BSD",
    keywords = "pycurl curl network parsing grabbing scraping lxml xpath",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
