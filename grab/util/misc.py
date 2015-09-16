import re


def camel_case_to_underscore(name):
    """Converts camel_case into CamelCase"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
