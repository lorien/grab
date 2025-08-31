from .client import HttpClient
from .extensions import CookiesExtension


class Grab(HttpClient):
    cookies = CookiesExtension()
