"""The Document class is the result of network request made with Grab instance."""

from __future__ import annotations

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
from copy import copy, deepcopy
from http.cookiejar import Cookie
from io import BytesIO, StringIO
from re import Match, Pattern
from typing import Any, TypedDict, cast
from urllib.parse import SplitResult, parse_qs, urljoin, urlsplit

import unicodec  # pylint: disable=wrong-import-order
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

from .base import BaseResponse
from .errors import DataNotFound, GrabMisuseError

THREAD_STORAGE = threading.local()
logger = logging.getLogger("grab.document")
UNDEFINED = object()


class FormRequestParams(TypedDict):
    url: str
    method: str
    multipart: bool
    fields: Sequence[tuple[str, Any]]


def normalize_pairs(
    inp: Sequence[tuple[str, Any]] | Mapping[str, Any]
) -> Sequence[tuple[str, Any]]:
    # pylint: disable=deprecated-typing-alias
    return list(inp.items()) if isinstance(inp, typing.Mapping) else inp


class Document(
    BaseResponse
):  # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """Network response."""

    __slots__ = (
        "document_type",
        "code",
        "head",
        "headers",
        "url",
        "cookies",
        "encoding",
        "_bytes_body",
        "_unicode_body",
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
    )

    def __init__(
        self,
        body: bytes,
        *,
        document_type: None | str = "html",
        head: None | bytes = None,
        headers: None | email.message.Message = None,
        encoding: None | str = None,
        code: None | int = None,
        url: None | str = None,
        cookies: None | Sequence[Cookie] = None,
    ) -> None:
        # Cache attributes
        self._unicode_body: None | str = None
        self._lxml_tree: None | _Element = None
        self._strict_lxml_tree: None | _Element = None
        self._pyquery = None
        self._lxml_form: None | FormElement = None
        self._file_fields: MutableMapping[str, Any] = {}
        # Main attributes
        self.document_type = document_type
        if not isinstance(body, bytes):
            raise ValueError("Argument 'body' must be bytes")
        self._bytes_body = body
        self.code = code
        self.head = head
        self.headers: email.message.Message = headers or email.message.Message()
        self.url = url
        # Encoding must be processed AFTER body and headers are set
        self.encoding = self.process_encoding(encoding)
        # other
        self.cookies = cookies or []
        self.download_size = 0
        self.upload_size = 0
        self.download_speed = 0
        self.error_code = None
        self.error_msg = None
        self.from_cache = False

    # WTF
    def __call__(self, query: str) -> SelectorList[_Element]:
        return self.select(query)

    def select(self, *args: Any, **kwargs: Any) -> SelectorList[_Element]:
        return XpathSelector(self.tree).select(*args, **kwargs)

    def process_encoding(self, encoding: None | str = None) -> str:
        """Process explicitly defined encoding or auto-detect it.

        If encoding is explicitly defined, ensure it is a valid encoding the python
        can deal with. If encoding is not specified, auto-detect it.

        Raises unicodec.InvalidEncodingName if explicitly set encoding is invalid.
        """
        if encoding:
            return unicodec.normalize_encoding_name(encoding)
        return unicodec.detect_content_encoding(
            self.get_body_chunk() or b"",
            content_type_header=(
                self.headers.get("Content-Type", None) if self.headers else None
            ),
            markup="xml" if self.document_type == "xml" else "html",
        )

    def copy(self) -> Document:
        return self.__class__(
            code=self.code,
            head=self.head,
            body=self.body,
            url=self.url,
            headers=deepcopy(self.headers),
            encoding=self.encoding,
            document_type=self.document_type,
            cookies=copy(self.cookies),
        )

    def save(self, path: str) -> None:
        """Save response body to file."""
        path_dir = os.path.split(path)[0]
        if not os.path.exists(path_dir):
            with suppress(OSError):
                os.makedirs(path_dir)

        with open(path, "wb") as out:
            out.write(self.body)

    @property
    def status(self) -> None | int:
        return self.code

    @status.setter
    def status(self, val: int) -> None:
        self.code = val

    @property
    def json(self) -> Any:
        """Return response body deserialized into JSON object."""
        assert self.body is not None
        return json.loads(self.body.decode(self.encoding))

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
        state: dict[str, Any] = {}
        for cls in type(self).mro():
            cls_slots = getattr(cls, "__slots__", ())
            for slot_name in cls_slots:
                if hasattr(self, slot_name):
                    state[slot_name] = getattr(self, slot_name)
        state["_lxml_tree"] = None
        state["_strict_lxml_tree"] = None
        state["_lxml_form"] = None
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        # TODO: check assigned key is in slots
        for slot_name, value in state.items():
            setattr(self, slot_name, value)

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
            return anchor in self.unicode_body()
        return anchor in self.body

    def text_assert(self, anchor: str | bytes) -> None:
        """If `anchor` is not found then raise `DataNotFound` exception."""
        if not self.text_search(anchor):
            raise DataNotFound("Substring not found: {}".format(str(anchor)))

    def text_assert_any(self, anchors: Sequence[str | bytes]) -> None:
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
        default: Any = UNDEFINED,
    ) -> Any:
        """Return content of first matching group of regexp found in response body."""
        try:
            match = self.rex_search(regexp, flags=flags)
        except DataNotFound as ex:
            if default is UNDEFINED:
                raise DataNotFound("Regexp not found") from ex
            return default
        else:
            return match.group(1)

    def rex_search(
        self,
        regexp: str | bytes | Pattern[str] | Pattern[bytes],
        flags: int = 0,
        default: Any = UNDEFINED,
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
            else regexp.search(self.unicode_body())
        )
        if match:
            return match
        if default is UNDEFINED:
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

    def get_body_chunk(self) -> bytes:
        return self.body[:4096]

    def unicode_body(
        self,
    ) -> str:
        """Return response body as unicode string."""
        if not self._unicode_body:
            # FIXME: ignore_errors option
            self._unicode_body = unicodec.decode_content(
                self.body, encoding=self.encoding
            )
        return self._unicode_body

    @property
    def body(self) -> bytes:
        return self._bytes_body

    @body.setter
    def body(self, body: bytes) -> None:
        raise GrabMisuseError("Document body could be set only in constructor")

    # DomTreeExtension methods

    @property
    def tree(self) -> _Element:
        """Return DOM tree of the document built with HTML DOM builder."""
        if self.document_type == "xml":
            return self.build_xml_tree()
        return self.build_html_tree()

    @classmethod
    def wrap_io(cls, inp: bytes | str) -> StringIO | BytesIO:
        return BytesIO(inp) if isinstance(inp, bytes) else StringIO(inp)

    @classmethod
    def _build_dom(cls, content: bytes | str, mode: str, encoding: str) -> _Element:
        assert mode in {"html", "xml"}
        if mode == "html":
            if not hasattr(THREAD_STORAGE, "html_parsers"):
                THREAD_STORAGE.html_parsers = {}
            parser = THREAD_STORAGE.html_parsers.setdefault(
                encoding, HTMLParser(encoding=encoding)
            )
            dom = etree.parse(cls.wrap_io(content), parser=parser)
            return dom.getroot()
        if not hasattr(THREAD_STORAGE, "xml_parser"):
            THREAD_STORAGE.xml_parsers = {}
        parser = THREAD_STORAGE.xml_parsers.setdefault(
            encoding, etree.XMLParser(resolve_entities=False)
        )
        dom = etree.parse(cls.wrap_io(content), parser=parser)
        return dom.getroot()

    def build_html_tree(self) -> _Element:
        if self._lxml_tree is None:
            assert self.body is not None
            ubody = self.unicode_body()
            body: None | bytes = (
                ubody.encode(self.encoding) if ubody is not None else None
            )
            if not body:
                # Generate minimal empty content
                # which will not break lxml parser
                body = b"<html></html>"
            try:
                self._lxml_tree = self._build_dom(body, "html", self.encoding)
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
                    self._lxml_tree = self._build_dom(body, "html", self.encoding)
                else:
                    raise
        return self._lxml_tree

    def build_xml_tree(self) -> _Element:
        if self._strict_lxml_tree is None:
            ubody = self.unicode_body()
            assert ubody is not None
            body = ubody.encode(self.encoding)
            self._strict_lxml_tree = self._build_dom(body, "xml", self.encoding)
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

            g.request('some URL')
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

    def get_cached_form(self) -> FormElement:
        """Get form which has been already selected.

        Returns None if form has not been selected yet.

        It is for testing mainly. To not trigger pylint warnings about
        accessing protected element.
        """
        if self._lxml_form is None:
            raise ValueError("Requested form does not exist")
        assert isinstance(self._lxml_form, FormElement)
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
    ) -> FormRequestParams:
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
        if extra_post:
            post_items = self.process_extra_post(
                post_items, normalize_pairs(extra_post)
            )
        if remove_from_post:
            post_items = [(x, y) for x, y in post_items if x not in remove_from_post]
        return {
            "url": action_url,
            "method": self.form.method.upper(),
            "multipart": "multipart" in self.form.get("enctype", ""),
            "fields": post_items,
        }

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
