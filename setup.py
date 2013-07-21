from setuptools import setup, find_packages
import re
import os

ROOT = os.path.dirname(os.path.realpath(__file__))
version = __import__('grab').__version__

setup(
    name = 'grab',
    version = version,
    description = 'Site Scraping Framework',
    long_description = open(os.path.join(ROOT, 'README.rst')).read(),
    url = 'http://github.com/lorien/grab',
    author = 'Grigory Petukhov',
    author_email = 'lorien@lorien.name',

    packages = find_packages(),
    include_package_data = True,
    scripts = ('bin/grab',),

    license = "BSD",
    keywords = "pycurl multicurl curl network parsing grabbing scraping lxml xpath",
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
