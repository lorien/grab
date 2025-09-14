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
        "selection>=2.0.1",
        'lxml;platform_system!="Windows"',
        'pycurl;platform_system!="Windows"',
        "defusedxml",
        'typing-extensions; python_version <= "2.7"',
    ],
    extras_require={
        "full": ["urllib3", "certifi"],
    },
)
