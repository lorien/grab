import re


RE_TOKEN1 = re.compile(r'(.)([A-Z][a-z]+)')
RE_TOKEN2 = re.compile(r'([a-z0-9])([A-Z])')


def camel_case_to_underscore(name):
    """Converts camel_case into CamelCase"""
    res = RE_TOKEN1.sub(r'\1_\2', name)
    res = RE_TOKEN2.sub(r'\1_\2', res)
    return res.lower()
