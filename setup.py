from setuptools import setup

setup(
    name="grab",
    version="0.6.41",
    packages=[
        "grab",
        "grab.script",
        "grab.spider",
        "grab.spider.cache_backend",
        "grab.spider.queue_backend",
        "grab.spider.network_service",
        "grab.transport",
        "grab.util",
    ],
    install_requires=[
        "weblib>=0.1.28",
        "six",
        "user_agent",
        "selection",
        'lxml;platform_system!="Windows"',
        'pycurl<7.43.0.2;platform_system!="Windows"',
        "defusedxml",
    ],
    extras_require={
        "full": ["urllib3", "certifi"],
    },
)
