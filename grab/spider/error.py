class SpiderError(Exception):
    "Base class for Spider exceptions"

class SpiderMisuseError(SpiderError):
    "Improper usage of Spider framework"

class FatalError(SpiderError):
    "Fatal error which should stop parsing process"
