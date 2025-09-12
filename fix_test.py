import re
from glob import glob

# self.server.response["get.data"] = "Simple String"

RE_DATA = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']data["\']\]\s*=\s*["\'](.+?)["\']',
    re.M,
)
RE_GET_DATA = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']get\.data["\']\]\s*=\s*["\'](.+?)["\']',
    re.M,
)
RE_DATA_VAR = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']data["\']\]\s*=\s*(\w+)$',
    re.M,
)
RE_GET_DATA_VAR = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']get\.data["\']\]\s*=\s*(\w+)$',
    re.M,
)
RE_HEADERS = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']headers["\']\]\s*=\s*(\[[^\]]+\])',
    re.M,
)
RE_COOKIES_DICT = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']cookies["\']\]\s*=\s*(\{[^\}]+\}\.items\(\))',
    re.M,
)
RE_COOKIES_DICT_EMPTY = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']cookies["\']\]\s*=\s*(\{\})',
    re.M,
)
RE_COOKIES_LIST = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']cookies["\']\]\s*=\s*(\[[^\]]*\])',
    re.M,
)
RE_CODE = re.compile(
    r'^(\s+)self\.server\.response(_once)?\[["\']code["\']\]\s*=\s*(\d+)',
    re.M,
)
RE_IMPORT = re.compile(r"^(from tests\.util)", re.M)
RE_ASSERT_REQUEST_ATTR = re.compile(
    r"^(\s*)(self\.assert[^\n]+)self\.server\.request"
    r'\[["\'](path|headers|cookies|data|method|args|files)["\']\]',
    re.M,
)


def handler_data(match):
    # fmt: off
    print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(data="{}"), count=1)'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_get_data(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(data="{}"), count=1, method="get")'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_get_data_var(match):
    # fmt: off
    print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(data={}), count=1, method="get")'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_data_var(match):
    # fmt: off
    print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(data={}))'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_headers(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(headers={}), count=1)'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_cookies(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(cookies={}), count=1)'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_code(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'{}self.server.add_response(Response(status={}), count=1)'.format(
        match.group(1),
        match.group(3),
    )
    # fmt: on


def handler_import(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'from test_server import Request, Response\n{}'.format(
        match.group(1),
    )
    # fmt: on


def handler_assert_request_attr(match):
    # fmt: off
    #print(u"Fixing line: {}".format(match.group(0)))
    return u'{}req = self.server.get_request()\n{}{}req.{}'.format(
        match.group(1),
        match.group(1),
        match.group(2),
        match.group(3)
    )
    # fmt: on


def process_file(path):
    print("--- {}".format(path))
    with open(path, "rb") as inp:
        content = inp.read().decode("utf-8")
        new_content = content
        new_content = RE_DATA.sub(handler_data, new_content)
        new_content = RE_GET_DATA.sub(handler_get_data, new_content)
        new_content = RE_GET_DATA_VAR.sub(handler_get_data_var, new_content)
        new_content = RE_DATA_VAR.sub(handler_data_var, new_content)
        new_content = RE_HEADERS.sub(handler_headers, new_content)
        new_content = RE_COOKIES_DICT.sub(handler_cookies, new_content)
        new_content = RE_COOKIES_DICT_EMPTY.sub(handler_cookies, new_content)
        new_content = RE_COOKIES_LIST.sub(handler_cookies, new_content)
        new_content = RE_CODE.sub(handler_code, new_content)
        new_content = RE_ASSERT_REQUEST_ATTR.sub(
            handler_assert_request_attr, new_content
        )
        if new_content != content:
            new_content = RE_IMPORT.sub(handler_import, new_content, count=1)
        new_path = path.replace("tests/", "fix/")
        with open(new_path, "wb") as out:
            out.write(new_content.encode("utf-8"))


def main():
    for path in glob("tests/*.py"):
        if "__init__" not in path:
            process_file(path)


if __name__ == "__main__":
    main()
