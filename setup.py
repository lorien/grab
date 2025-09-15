from setuptools import setup

setup(
    name="grab",
    version="1.0.1",
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
        "six",
        "user_agent",
        "selection>=2.0.1",
        'lxml;platform_system != "Windows" or python_version >= "3.13"',
        'pycurl;platform_system != "Windows" or python_version >= "3.13"',
        "defusedxml",
        'typing-extensions; python_version <= "2.7"',
    ],
    extras_require={
        "full": [  # deprecated
            "urllib3",
            "certifi",
        ],
        "urllib3": [
            "urllib3",
            "certifi",
        ],
        "pyquery": [
            'pyquery; platform_system != "Windows" and python_version >= "3.0"',
            'pyquery; platform_system == "Windows" and python_version >= "3.13"',
            'pyquery <= 1.4.1; platform_system != "Windows" and python_version <= "2.7"',
        ],
    },
)
