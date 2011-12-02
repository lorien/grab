class SpiderError(Exception):
    "Base class for Spider exceptions"


class SpiderMisuseError(SpiderError):
    "Improper usage of Spider framework"
