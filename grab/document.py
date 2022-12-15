# Copyright: 2013, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: MIT
# pylint: disable=too-many-lines
"""The Document class is the result of network request made with Grab instance."""
from __future__ import annotations

import codecs
import email
import email.message
import json
import logging
import os
import re
import tempfile
import threading
import typing
import webbrowser
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import suppress
from copy import copy
from datetime import datetime
from io import BytesIO, StringIO
from pprint import pprint  # pylint: disable=unused-import
from re import Match, Pattern
from typing import IO, Any, Protocol, cast
from urllib.parse import SplitResult, parse_qs, urlencode, urljoin, urlsplit

from lxml import etree
from lxml.etree import _Element
from lxml.html import (
    CheckboxValues,
    FormElement,
    HtmlElement,
    HTMLParser,
    MultipleSelectOptions,
)
from selection import SelectorList, XpathSelector

from grab.cookie import CookieManager
from grab.error import DataNotFound, GrabFeatureIsDeprecated, GrabMisuseError
from grab.types import NULL, GrabConfig
from grab.util.encoding import read_bom
from grab.util.files import hashed_path
from grab.util.html import decode_entities, find_refresh_url
from grab.util.html import fix_special_entities as fix_special_entities_func
from grab.util.text import normalize_spaces
from grab.util.warning import warn

NULL_BYTE = chr(0)
RE_XML_DECLARATION = re.compile(rb"^[^<]{,100}<\?xml[^>]+\?>", re.I)
RE_DECLARATION_ENCODING = re.compile(rb'encoding\s*=\s*["\']([^"\']+)["\']')
RE_META_CHARSET = re.compile(rb"<meta[^>]+content\s*=\s*[^>]+charset=([-\w]+)", re.I)
RE_META_CHARSET_HTML5 = re.compile(rb'<meta[^>]+charset\s*=\s*[\'"]?([-\w]+)', re.I)
RE_UNICODE_XML_DECLARATION = re.compile(
    RE_XML_DECLARATION.pattern.decode("utf-8"), re.I
)

THREAD_STORAGE = threading.local()
logger = logging.getLogger("grab.document")


class GrabConfigProtocol(Protocol):
    config: GrabConfig


def normalize_pairs(
    inp: Sequence[tuple[str, Any]] | Mapping[str, Any]
) -> Sequence[tuple[str, Any]]:
    # pylint: disable=deprecated-typing-alias
    return list(inp.items()) if isinstance(inp, typing.Mapping) else inp


class Document:  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Network response."""

    __slots__ = (
        "status",
        "code",
        "head",
        "_bytes_body",
        "body_path",
        "headers",
        "url",
        "cookies",
        "charset",
        "_unicode_body",
        "bom",
        "timestamp",
        "name_lookup_time",
        "connect_time",
        "total_time",
        "download_size",
        "upload_size",
        "download_speed",
        "error_code",
        "error_msg",
        "grab",
        "remote_ip",
        "_lxml_tree",
        "_strict_lxml_tree",
        "_pyquery",
        "_lxml_form",
        "_file_fields",
        "from_cache",
        "_grab_config",
    )

    def __init__(self, grab: None | GrabConfigProtocol = None) -> None:
        self._grab_config: GrabConfig = {}
        if grab:
            self.process_grab_config(grab.config)
        self.status: None | str = None
        self.code: None | int = None
        self.head: None | bytes = None
        self.headers: None | email.message.Message = None
        self.url: None | str = None
        self.cookies = CookieManager()
        self.charset = "utf-8"
        self.bom: None | bytes = None
        self.timestamp = datetime.utcnow()
        self.name_lookup_time = 0
        self.connect_time = 0
        self.total_time = 0
        self.download_size = 0
        self.upload_size = 0
        self.download_speed = 0
        self.error_code = None
        self.error_msg = None
        self.from_cache = False

        # Body
        self.body_path: None | str = None
        self._bytes_body: None | bytes = None
        self._unicode_body: None | str = None

        # DOM Tree
        self._lxml_tree: None | _Element = None
        self._strict_lxml_tree: None | _Element = None

        # Pyquery
        self._pyquery = None

        # Form
        self._lxml_form = None
        self._file_fields: MutableMapping[str, Any] = {}

    def process_grab_config(self, grab_config: Mapping[str, Any]) -> Any:
        # Save some grab.config items required to
        # process content of the document
        for key in (
            "content_type",
            "fix_special_entities",
            "lowercased_tree",
            "strip_null_bytes",
        ):
            self._grab_config[key] = grab_config[key]

    # WTF
    def __call__(self, query: str) -> SelectorList[_Element]:
        return self.select(query)

    def select(self, *args: Any, **kwargs: Any) -> SelectorList[_Element]:
        return XpathSelector(self.tree).select(*args, **kwargs)

    def parse(
        self,
        charset: None | str = None,
        headers: None | email.message.Message = None,
    ) -> None:
        """Parse headers.

        This method is called after Grab instance performs network request.
        """
        if headers:
            self.headers = headers
        else:
            # WTF: It is curl-related, I think
            # Parse headers only from last response
            # There could be multiple responses in `self.head`
            # in case of 301/302 redirect
            # Separate responses
            if self.head:
                responses = self.head.rsplit(b"\nHTTP/", 1)
                # Cut off the 'HTTP/*' line from the last response
                _, response_bytes = responses[-1].split(b"\n", 1)
                response = response_bytes.decode("utf-8", "ignore")
            else:
                response = ""
            self.headers = email.message_from_string(response)

        if charset is None:
            if isinstance(self.body, str):
                self.charset = "utf-8"
            else:
                self.detect_charset()
        else:
            self.charset = charset.lower()

        self._unicode_body = None

    def detect_charset_from_body_chunk(
        self, body_chunk: bytes
    ) -> tuple[None | str, None | bytes]:
        charset: None | str = None
        ret_bom: None | bytes = None
        # Try to extract charset from http-equiv meta tag
        match_charset = RE_META_CHARSET.search(body_chunk)
        if match_charset:
            charset = match_charset.group(1).decode("utf-8", "ignore")
        else:
            match_charset_html5 = RE_META_CHARSET_HTML5.search(body_chunk)
            if match_charset_html5:
                charset = match_charset_html5.group(1).decode("utf-8", "ignore")

        # TODO: <meta charset="utf-8" />
        bom_encoding, chunk_bom = read_bom(body_chunk)
        if bom_encoding:
            charset = bom_encoding
            ret_bom = chunk_bom

        # Try to process XML declaration
        if not charset and body_chunk.startswith(b"<?xml"):
            match = RE_XML_DECLARATION.search(body_chunk)
            if match:
                enc_match = RE_DECLARATION_ENCODING.search(match.group(0))
                if enc_match:
                    charset = cast(bytes, enc_match.group(1)).decode("utf-8", "ignore")
        return charset, ret_bom

    def detect_charset(self) -> None:
        """Detect charset of the response. Set charset inplace to "self.charset".

        Try following methods:
        * meta[name="Http-Equiv"]
        * XML declaration
        * HTTP Content-Type header

        Ignore unknown charsets.

        Use utf-8 as fallback charset.
        """
        charset = None

        body_chunk = self.get_body_chunk()

        if body_chunk:
            charset, bom = self.detect_charset_from_body_chunk(body_chunk)
            if bom:
                self.bom = bom

        if not charset and self.headers and "Content-Type" in self.headers:
            pos = self.headers["Content-Type"].find("charset=")
            if pos > -1:
                charset = self.headers["Content-Type"][(pos + 8) :]

        if charset:
            charset = charset.lower()
            if not isinstance(charset, str):
                # Convert to unicode (py2.x) or string (py3.x)
                charset = charset.decode("utf-8")
            # Check that python knows such charset
            try:
                codecs.lookup(charset)
            except LookupError:
                logger.debug("Unknown charset found: %s. Using utf-8 instead.", charset)
                self.charset = "utf-8"
            else:
                self.charset = charset

    def copy(self, new_grab_config: None | GrabConfig = None) -> Document:
        """Clone the Response object."""
        if new_grab_config.__class__.__name__ == "Grab":
            raise GrabFeatureIsDeprecated(
                "Method Document.copy does not accept Grab instance"
                " as second parameter anymore. It accepts now"
                " Grab.config instance."
            )
        obj = self.__class__()
        copy_keys = (
            "status",
            "code",
            "head",
            "body",
            "total_time",
            "connect_time",
            "name_lookup_time",
            "url",
            "charset",
            "_unicode_body",
            "_grab_config",
        )
        for key in copy_keys:
            setattr(obj, key, getattr(self, key))
        obj.process_grab_config(new_grab_config or self._grab_config)
        obj.headers = copy(self.headers)
        # TODO: Maybe, deepcopy?
        obj.cookies = copy(self.cookies)
        return obj

    def save(self, path: str) -> None:
        """Save response body to file."""
        path_dir = os.path.split(path)[0]
        if not os.path.exists(path_dir):
            with suppress(OSError):
                os.makedirs(path_dir)

        with open(path, "wb") as out:
            out.write(self._bytes_body if self._bytes_body is not None else b"")

    def save_hash(self, location: str, basedir: str, ext: None | str = None) -> str:
        """Save response body into file with special path built from hash.

        That allows to lower number of files
        per directory.

        :param location: URL of file or something else. It is
            used to build the SHA1 hash.
        :param basedir: base directory to save the file. Note that
            file will not be saved directly to this directory but to
            some sub-directory of `basedir`
        :param ext: extension which should be appended to file name. The
            dot is inserted automatically between filename and extension.
        :returns: path to saved file relative to `basedir`

        Example::

            >>> url = 'http://yandex.ru/logo.png'
            >>> g.go(url)
            >>> g.response.save_hash(url, 'some_dir', ext='png')
            'e8/dc/f2918108788296df1facadc975d32b361a6a.png'
            # the file was saved to $PWD/some_dir/e8/dc/...

        TODO: replace `basedir` with two options: root and save_to. And
        returns save_to + path
        """
        rel_path = hashed_path(location, ext=ext)
        path = os.path.join(basedir, rel_path)
        if not os.path.exists(path):
            path_dir, _ = os.path.split(path)
            with suppress(OSError):
                os.makedirs(path_dir)
            with open(path, "wb") as out:
                out.write(cast(bytes, self._bytes_body))
        return rel_path

    @property
    def json(self) -> Any:
        """Return response body deserialized into JSON object."""
        assert self.body is not None
        return json.loads(self.body.decode(self.charset))

    def url_details(self) -> SplitResult:
        """Return result of urlsplit function applied to response url."""
        return urlsplit(cast(str, self.url))

    def query_param(self, key: str) -> str:
        """Return value of parameter in query string."""
        return parse_qs(self.url_details().query)[key][0]

    def browse(self) -> None:
        """Save response in temporary file and open it in GUI browser."""
        _, path = tempfile.mkstemp()
        self.save(path)
        webbrowser.open("file://" + path)

    def __getstate__(self) -> Mapping[str, Any]:
        """Reset cached lxml objects which could not be pickled."""
        state = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot in cls_slots:
                if slot != "__weakref__" and hasattr(self, slot):
                    state[slot] = getattr(self, slot)
        state["_lxml_tree"] = None
        state["_strict_lxml_tree"] = None
        state["_lxml_form"] = None
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for slot, value in state.items():
            setattr(self, slot, value)

    def get_meta_refresh_url(self) -> None | str:
        return find_refresh_url(cast(str, self.unicode_body()))

    # TextExtension methods

    def text_search(self, anchor: str | bytes) -> bool:
        """Search the substring in response body.

        :param anchor: string to search
        :param byte: if False then `anchor` should be the
            unicode string, and search will be performed in
            `response.unicode_body()` else `anchor` should be the byte-string
            and search will be performed in `response.body`

        If substring is found return True else False.
        """
        assert self.body is not None
        if isinstance(anchor, str):
            return anchor in cast(str, self.unicode_body())
        return anchor in self.body

    def text_assert(self, anchor: str | bytes) -> None:
        """If `anchor` is not found then raise `DataNotFound` exception."""
        if not self.text_search(anchor):
            raise DataNotFound("Substring not found: {}".format(str(anchor)))

    def text_assert_any(self, anchors: list[str | bytes]) -> None:
        """If no `anchors` were found then raise `DataNotFound` exception."""
        if not any(self.text_search(x) for x in anchors):
            raise DataNotFound(
                "Substrings not found: %s" % ", ".join(map(str, anchors))
            )

    # RegexpExtension methods

    def rex_text(
        self,
        regexp: str | bytes | Pattern[str] | Pattern[bytes],
        flags: int = 0,
        default: Any = NULL,
    ) -> Any:
        """Return content of first matching group of regexp found in response body."""
        try:
            match = self.rex_search(regexp, flags=flags)
        except DataNotFound as ex:
            if default is NULL:
                raise DataNotFound("Regexp not found") from ex
            return default
        else:
            return normalize_spaces(decode_entities(match.group(1)))

    def rex_search(
        self,
        regexp: str | bytes | Pattern[str] | Pattern[bytes],
        flags: int = 0,
        default: Any = NULL,
    ) -> Any:
        """Search the regular expression in response body.

        Return found match object or None
        """
        match: None | Match[bytes] | Match[str] = None
        assert self.body is not None
        if isinstance(regexp, (bytes, str)):
            regexp = re.compile(regexp, flags=flags)
        match = (
            regexp.search(self.body)
            if isinstance(regexp.pattern, bytes)
            else regexp.search(cast(str, self.unicode_body()))
        )
        if match:
            return match
        if default is NULL:
            raise DataNotFound("Could not find regexp: %s" % regexp)
        return default

    def rex_assert(
        self,
        rex: str | bytes | Pattern[str] | Pattern[bytes],
    ) -> None:
        """Raise `DataNotFound` exception if `rex` expression is not found."""
        # if given regexp not found, rex_search() will raise DataNotFound
        # because default argument is not set
        self.rex_search(rex)

    # PyqueryExtension methods

    @property
    def pyquery(self) -> Any:
        """Return pyquery handler."""
        if not self._pyquery:
            # pytype: disable=import-error
            from pyquery import PyQuery  # pylint: disable=import-outside-toplevel

            # pytype: enable=import-error

            self._pyquery = PyQuery(self.tree)
        return self._pyquery

    # BodyExtension methods

    def get_body_chunk(self) -> None | bytes:
        if self.body_path:
            with open(self.body_path, "rb") as inp:
                return inp.read(4096)
        elif self._bytes_body:
            return self._bytes_body[:4096]
        return None

    def convert_body_to_unicode(
        self,
        body: bytes,
        bom: None | bytes,
        charset: str,
        ignore_errors: bool,
        fix_special_entities: bool,
    ) -> str:
        # WTF: How could it be unicode???
        # if isinstance(body, unicode):
        # body = body.encode('utf-8')
        if bom is not None:
            body = body[len(bom) :]
        if fix_special_entities:
            body = fix_special_entities_func(body)
        errors = "ignore" if ignore_errors else "strict"
        return body.decode(charset, errors).strip()

    def read_body_from_file(self) -> bytes:
        with open(cast(str, self.body_path), "rb") as inp:
            return cast(IO[bytes], inp).read()

    def unicode_body(
        self, ignore_errors: bool = True, fix_special_entities: bool = True
    ) -> None | str:
        """Return response body as unicode string."""
        if self.body is None:
            return None
        if not self._unicode_body:
            self._unicode_body = self.convert_body_to_unicode(
                body=self.body,
                bom=self.bom,
                charset=self.charset,
                ignore_errors=ignore_errors,
                fix_special_entities=fix_special_entities,
            )
        return self._unicode_body

    @property
    def body(self) -> None | bytes:
        if self.body_path:
            return self.read_body_from_file()
        return cast(bytes, self._bytes_body)

    @body.setter
    def body(self, body: bytes) -> None:
        if isinstance(body, str):
            raise GrabMisuseError("Document.body could be only byte string.")
        if self.body_path:
            with open(self.body_path, "wb") as out:
                out.write(body)
            self._bytes_body = None
        else:
            self._bytes_body = body
        self._unicode_body = None

    # DomTreeExtension methods

    @property
    def tree(self) -> _Element:
        """Return DOM tree of the document built with HTML DOM builder."""
        if self._grab_config["content_type"] == "xml":
            return self.build_xml_tree()
        return self.build_html_tree()

    @classmethod
    def wrap_io(cls, inp: bytes | str) -> StringIO | BytesIO:
        return BytesIO(inp) if isinstance(inp, bytes) else StringIO(inp)

    @classmethod
    def _build_dom(cls, content: bytes | str, mode: str, charset: str) -> _Element:
        assert mode in {"html", "xml"}
        if mode == "html":
            if not hasattr(THREAD_STORAGE, "html_parsers"):
                THREAD_STORAGE.html_parsers = {}
            parser = THREAD_STORAGE.html_parsers.setdefault(
                charset, HTMLParser(encoding=charset)
            )
            dom = etree.parse(cls.wrap_io(content), parser=parser)
            return dom.getroot()
        if not hasattr(THREAD_STORAGE, "xml_parser"):
            THREAD_STORAGE.xml_parsers = {}
        parser = THREAD_STORAGE.xml_parsers.setdefault(
            charset, etree.XMLParser(resolve_entities=False)
        )
        dom = etree.parse(cls.wrap_io(content), parser=parser)
        return dom.getroot()

    def build_html_tree(self) -> _Element:
        if self._lxml_tree is None:
            assert self.body is not None
            body = self.body
            fix_setting = self._grab_config["fix_special_entities"]
            # body = self.unicode_body(fix_special_entities=fix_setting).strip()
            if fix_setting:
                body = fix_special_entities_func(body)
            if self._grab_config["lowercased_tree"]:
                body = body.lower()
            # could not be applied to bytes body
            # if self._grab_config["strip_null_bytes"]:
            #    body = body.replace(NULL_BYTE, "")
            body = RE_XML_DECLARATION.sub(b"", body)
            if not body:
                # Generate minimal empty content
                # which will not break lxml parser
                body = b"<html></html>"
            try:
                self._lxml_tree = self._build_dom(body, "html", self.charset)
            except Exception as ex:
                # FIXME: write test for this case
                if b"<html" not in body and (
                    # Fix for "just a string" body
                    (
                        isinstance(ex, etree.ParserError)
                        and "Document is empty" in str(ex)
                    )
                    # Fix for smth like "<frameset></frameset>"
                    or (
                        isinstance(ex, TypeError)
                        and "object of type 'NoneType' has no len" in str(ex)
                    )
                ):
                    body = b"<html>%s</html>" % body
                    self._lxml_tree = self._build_dom(body, "html", self.charset)
                else:
                    raise
        return self._lxml_tree

    @property
    def xml_tree(self) -> _Element:
        """Return DOM-tree of the document built with XML DOM builder."""
        warn(
            "Attribute `grab.xml_tree` is deprecated. "
            "Use `Grab.doc.tree` attribute "
            'AND content_type="xml" option instead.'
        )
        return self.build_xml_tree()

    def build_xml_tree(self) -> _Element:
        if self._strict_lxml_tree is None:
            assert self.body is not None
            self._strict_lxml_tree = self._build_dom(self.body, "xml", self.charset)
        return self._strict_lxml_tree

    # FormExtension methods

    def choose_form(
        self,
        number: None | int = None,
        xpath: None | str = None,
        name: None | str = None,
        **kwargs: Any,
    ) -> None:
        """Set the default form.

        :param number: number of form (starting from zero)
        :param id: value of "id" attribute
        :param name: value of "name" attribute
        :param xpath: XPath query
        :raises: :class:`DataNotFound` if form not found
        :raises: :class:`GrabMisuseError`
            if method is called without parameters

        Selected form will be available via `form` attribute of `Grab`
        instance. All form methods will work with default form.

        Examples::

            # Select second form
            g.choose_form(1)

            # Select by id
            g.choose_form(id="register")

            # Select by name
            g.choose_form(name="signup")

            # Select by xpath
            g.choose_form(xpath='//form[contains(@action, "/submit")]')
        """
        idx = 0
        if kwargs.get("id") is not None:
            query = '//form[@id="{}"]'.format(kwargs["id"])
        elif name is not None:
            query = '//form[@name="{}"]'.format(name)
        elif number is not None:
            query = "//form"
            idx = number
        elif xpath is not None:
            query = xpath
        else:
            raise GrabMisuseError(
                "choose_form methods requires one of "
                "[number, id, name, xpath] arguments"
            )
        try:
            self._lxml_form = cast(HtmlElement, self.select(query)[idx].node())
        except IndexError as ex:
            raise DataNotFound("Could not find form with xpath: %s" % xpath) from ex

    @property
    def form(self) -> FormElement:
        """Return default document's form.

        If form was not selected manually then select the form
        which has the biggest number of input elements.

        The form value is just an `lxml.html` form element.

        Example::

            g.go('some URL')
            # Choose form automatically
            print g.form

            # And now choose form manually
            g.choose_form(1)
            print g.form
        """
        if self._lxml_form is None:
            forms = [
                (idx, len(list(x.fields)))
                for idx, x in enumerate(cast(HtmlElement, self.tree).forms)
            ]
            if forms:
                idx = sorted(forms, key=lambda x: x[1], reverse=True)[0][0]
                self.choose_form(idx)
            else:
                raise DataNotFound("Response does not contains any form")
        return self._lxml_form

    def get_cached_form(self) -> None | FormElement:
        """Get form which has been already selected.

        Returns None if form has not been selected yet.

        It is for testing mainly. To not trigger pylint warnings about
        accessing protected element.
        """
        return self._lxml_form

    def set_input(self, name: str, value: Any) -> None:
        """Set the value of form element by its `name` attribute.

        :param name: name of element
        :param value: value which should be set to element

        To check/uncheck the checkbox pass boolean value.

        Example::

            g.set_input('sex', 'male')

            # Check the checkbox
            g.set_input('accept', True)
        """
        if self._lxml_form is None:
            self.choose_form_by_element('.//*[@name="%s"]' % name)
        elem = self.form.inputs[name]

        processed = False
        if getattr(elem, "type", None) == "checkbox" and isinstance(value, bool):
            elem.checked = value
            processed = True

        if not processed:
            # We need to remember original values of file fields
            # Because lxml will convert UploadContent/UploadFile object to
            # string
            if getattr(elem, "type", "").lower() == "file":
                self._file_fields[name] = value
                elem.value = ""
            else:
                elem.value = value

    def set_input_by_id(self, _id: str, value: Any) -> None:
        """Set the value of form element by its `id` attribute.

        :param _id: id of element
        :param value: value which should be set to element
        """
        xpath = './/*[@id="%s"]' % _id
        if self._lxml_form is None:
            self.choose_form_by_element(xpath)
        sel = XpathSelector(self.form)
        elem = sel.select(xpath).node()
        return self.set_input(elem.get("name"), value)

    def set_input_by_number(self, number: int, value: Any) -> None:
        """Set the value of form element by its number in the form.

        :param number: number of element
        :param value: value which should be set to element
        """
        sel = XpathSelector(self.form)
        elem = sel.select('.//input[@type="text"]')[number].node()
        return self.set_input(elem.get("name"), value)

    def set_input_by_xpath(self, xpath: str, value: Any) -> None:
        """Set the value of form element by xpath.

        :param xpath: xpath path
        :param value: value which should be set to element
        """
        elem = self.select(xpath).node()

        if self._lxml_form is None:
            # Explicitly set the default form
            # which contains found element
            parent = elem
            while True:
                parent = parent.getparent()
                if parent.tag == "form":
                    self._lxml_form = parent
                    break

        return self.set_input(elem.get("name"), value)

    # FIXME:
    # * Remove set_input_by_id
    # * Remove set_input_by_number
    # * New method: set_input_by(id=None, number=None, xpath=None)

    def process_extra_post(
        self,
        post_items: list[tuple[str, Any]],
        extra_post_items: Sequence[tuple[str, Any]],
    ) -> list[tuple[str, Any]]:

        # Drop existing post items with such key
        keys_to_drop = {x for x, y in extra_post_items}
        for key in keys_to_drop:
            post_items = [(x, y) for x, y in post_items if x != key]

        for key, value in extra_post_items:
            post_items.append((key, value))
        return post_items

    def clean_submit_controls(
        self, post: MutableMapping[str, Any], submit_name: None | str
    ) -> None:
        # All this code need only for one reason:
        # to not send multiple submit keys in form data
        # in real life only this key is submitted whose button
        # was pressed

        # Build list of submit buttons which have a name
        submit_control_names: set[str] = set()
        for elem in self.form.inputs:
            if (
                elem.tag == "input"
                and elem.type == "submit"
                and elem.get("name") is not None
            ):
                submit_control_names.add(elem.name)

        if submit_control_names:
            # If name of submit control is not given then
            # use the name of first submit control
            if submit_name is None or submit_name not in submit_control_names:
                submit_name = sorted(submit_control_names)[0]

            # FIXME: possibly need to update post
            # if new submit_name is not in post

            # Form data should contain only one submit control
            for name in submit_control_names:
                if name != submit_name and name in post:
                    del post[name]

    def get_form_request(
        self,
        submit_name: None | str = None,
        url: None | str = None,
        extra_post: None | Mapping[str, Any] | Sequence[tuple[str, Any]] = None,
        remove_from_post: None | Sequence[str] = None,
    ) -> MutableMapping[str, Any]:
        """Submit default form.

        :param submit_name: name of button which should be "clicked" to
            submit form
        :param url: explicitly specify form action url
        :param extra_post: (dict or list of pairs) additional form data which
            will override data automatically extracted from the form.
        :param remove_from_post: list of keys to remove from the submitted data

        Following input elements are automatically processed:

        * input[type="hidden"] - default value
        * select: value of last option
        * radio - ???
        * checkbox - ???

        Multipart forms are correctly recognized by grab library.
        """
        post = self.form_fields()
        self.clean_submit_controls(post, submit_name)
        assert self.url is not None

        action_url = (
            urljoin(self.url, url) if url else urljoin(self.url, self.form.action)
        )

        # Values from `extra_post` should override values in form
        # `extra_post` allows multiple value of one key

        # Process saved values of file fields
        if self.form.method == "POST" and "multipart" in self.form.get("enctype", ""):
            for key, obj in self._file_fields.items():
                post[key] = obj

        post_items: list[tuple[str, Any]] = list(post.items())
        del post

        # extra_post_items = (
        #    cast(typing.Sequence[Tuple[str, Any]], extra_post.items())
        #    if isinstance(extra_post, Mapping)
        #    else extra_post
        # )

        if extra_post:
            post_items = self.process_extra_post(
                post_items, normalize_pairs(extra_post)
            )

        if remove_from_post:
            post_items = [(x, y) for x, y in post_items if x not in remove_from_post]

        result: MutableMapping[str, Any] = {
            "multipart_post": None,
            "post": None,
            "url": None,
        }

        if self.form.method == "POST":
            if "multipart" in self.form.get("enctype", ""):
                result["multipart_post"] = post_items
            else:
                result["post"] = post_items
            result["url"] = action_url

        else:
            url = action_url.split("?")[0] + "?" + urlencode(post_items)
            result["url"] = url

        return result

    def build_fields_to_remove(
        self, fields: Mapping[str, Any], form_inputs: Sequence[HtmlElement]
    ) -> set[str]:
        fields_to_remove: set[str] = set()
        for elem in form_inputs:
            # Ignore elements without name
            if not elem.get("name"):
                continue
            # Do not submit disabled fields
            # http://www.w3.org/TR/html4/interact/forms.html#h-17.12
            if elem.get("disabled") and elem.name in fields:
                fields_to_remove.add(elem.name)
            elif getattr(elem, "type", None) == "checkbox":
                if (
                    not elem.checked
                    and elem.name is not None
                    and elem.name in fields
                    and fields[elem.name] is None
                ):
                    fields_to_remove.add(elem.name)
            elif elem.name in fields_to_remove:
                # WHAT THE FUCK DOES THAT MEAN?
                fields_to_remove.remove(elem.name)
        return fields_to_remove

    def process_form_fields(self, fields: MutableMapping[str, Any]) -> None:
        for key, val in list(fields.items()):
            if isinstance(val, CheckboxValues):
                if not val:
                    del fields[key]
                elif len(val) == 1:
                    fields[key] = val.pop()
                else:
                    fields[key] = list(val)
            if isinstance(val, MultipleSelectOptions):
                if not val:
                    del fields[key]
                elif len(val) == 1:
                    fields[key] = val.pop()
                else:
                    fields[key] = list(val)

    def form_fields(self) -> MutableMapping[str, HtmlElement]:
        """Return fields of default form.

        Fill some fields with reasonable values.
        """
        fields = dict(self.form.fields)
        self.process_form_fields(fields)
        for elem in self.form.inputs:
            if (
                elem.tag == "select"
                and elem.name in fields
                and fields[elem.name] is None
                and elem.value_options
            ):
                fields[elem.name] = elem.value_options[0]
            elif (getattr(elem, "type", None) == "radio") and fields[elem.name] is None:
                fields[elem.name] = elem.get("value")
        for name in self.build_fields_to_remove(fields, self.form.inputs):
            del fields[name]
        return fields

    def choose_form_by_element(self, xpath: str) -> None:
        elem = self.select(xpath).node()
        while elem is not None:
            if elem.tag == "form":
                self._lxml_form = elem
                return
            elem = elem.getparent()
        self._lxml_form = None
