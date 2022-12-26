from pprint import pprint  # pylint: disable=unused-import
from urllib.parse import parse_qsl

from test_server import Response

from grab import DataNotFound, GrabMisuseError, request
from grab.document import Document
from tests.util import BaseTestCase

FORMS_HTML = b"""
<head>
    <title>Title</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
</head>
<body>
    <div id="header">
        <form id="search_form" method="GET">
            <input id="search_box" name="query" value="" />
            <input type="submit" value="submit" class="submit_btn"
                name="submit" />
        </form>
    </div>
    <div id="content">
        <FORM id="common_form" method="POST">
          <input type="text" id="some_value" name="some_value" value="" />
          <input id="some_value" name="image" type="file" value="" />
          <select id="gender" name="gender">
              <option value="1">Female</option>
              <option value="2">Male</option>
           </select>
           <input type="submit" value="submit" class="submit_btn"
            name="submit" />
        </FORM>
        <h1 id="fake_form">Big header</h1>
        <form name="dummy" action="/dummy">
           <input type="submit" value="submit" class="submit_btn"
            name="submit" />
           <input type="submit" value="submit2" class="submit_btn"
            name="submit" />
        </form>
    </div>
</body>
"""

POST_FORM = b"""
<form method="post" action="%s">
    <input type="text" name="secret" value="123"/>
    <input type="text" name="name" />
    <input type="text" disabled value="some_text" name="disabled_text" />
</form>
"""

MULTIPLE_SUBMIT_FORM = b"""
<form method="post">
    <input type="text" name="secret" value="123"/>
    <input type="submit" name="submit1" value="submit1" />
    <input type="submit" name="submit2" value="submit2" />
</form>
"""

NO_FORM_HTML = b"""
<div>Hello world</div>
"""

DISABLED_RADIO_HTML = b"""
<form>
    <input type="radio" name="foo" value="1" disabled="disabled" />
    <input type="radio" name="foo" value="2" disabled="disabled" />

    <input type="radio" name="bar" value="1" checked="checked" />
    <input type="radio" name="bar" value="2" disabled="disabled" />
</form>
"""


class TestHtmlForms(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

        # Create fake grab instance with fake response
        self.doc = Document(FORMS_HTML)

    def test_choose_form1(self) -> None:
        """Test ``choose_form`` method."""
        # raise errors
        self.assertRaises(DataNotFound, self.doc.choose_form, 10)
        self.assertRaises(DataNotFound, self.doc.choose_form, id="bad_id")
        self.assertRaises(DataNotFound, self.doc.choose_form, id="fake_form")
        self.assertRaises(GrabMisuseError, self.doc.choose_form)

        # check results
        self.doc.choose_form(0)
        self.assertEqual("form", self.doc.get_cached_form().tag)
        self.assertEqual("search_form", self.doc.get_cached_form().get("id"))

    def test_choose_form2(self) -> None:
        self.doc = Document(FORMS_HTML)

        self.doc.choose_form(id="common_form")
        self.assertEqual("form", self.doc.get_cached_form().tag)
        self.assertEqual("common_form", self.doc.get_cached_form().get("id"))

    def test_choose_form3(self) -> None:
        self.doc = Document(FORMS_HTML)

        self.doc.choose_form(name="dummy")
        self.assertEqual("form", self.doc.get_cached_form().tag)
        self.assertEqual("dummy", self.doc.get_cached_form().get("name"))

    def test_choose_form4(self) -> None:
        self.doc = Document(FORMS_HTML)

        self.doc.choose_form(xpath='//form[contains(@action, "/dummy")]')
        self.assertEqual("form", self.doc.get_cached_form().tag)
        self.assertEqual("dummy", self.doc.get_cached_form().get("name"))

    def assert_equal_qs(self, qs1: bytes, qs2: bytes) -> None:
        args1 = set(parse_qsl(qs1))
        args2 = set(parse_qsl(qs2))
        self.assertEqual(args1, args2)

    def test_submit(self) -> None:
        self.server.add_response(
            Response(data=POST_FORM % self.server.get_url().encode())
        )
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        doc.set_input("name", "Alex")
        request(**doc.get_form_request())
        self.assert_equal_qs(self.server.request.data, b"name=Alex&secret=123")

        # Default submit control
        self.server.add_response(Response(data=MULTIPLE_SUBMIT_FORM))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request())
        self.assert_equal_qs(self.server.request.data, b"secret=123&submit1=submit1")

        # Selected submit control
        self.server.add_response(Response(data=MULTIPLE_SUBMIT_FORM))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request(submit_name="submit2"))
        self.assert_equal_qs(self.server.request.data, b"secret=123&submit2=submit2")

        # Default submit control if submit control name is invalid
        self.server.add_response(Response(data=MULTIPLE_SUBMIT_FORM))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request(submit_name="submit3"))
        self.assert_equal_qs(self.server.request.data, b"secret=123&submit1=submit1")

    def test_submit_remove_from_post_argument(self) -> None:
        self.server.add_response(Response(data=MULTIPLE_SUBMIT_FORM))
        self.server.add_response(Response())

        doc = request(self.server.get_url())
        request(**doc.get_form_request(submit_name="submit3"))
        self.assert_equal_qs(self.server.request.data, b"secret=123&submit1=submit1")

        self.server.add_response(Response(data=MULTIPLE_SUBMIT_FORM))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request(remove_from_post=["submit1"]))
        self.assert_equal_qs(self.server.request.data, b"secret=123")

    def test_set_methods1(self) -> None:
        self.server.add_response(Response(data=FORMS_HTML))
        doc = request(self.server.get_url())

        with self.assertRaises(ValueError):
            doc.get_cached_form()

        doc.set_input("gender", "1")
        self.assertEqual("common_form", doc.get_cached_form().get("id"))

        self.assertRaises(KeyError, lambda: doc.set_input("query", "asdf"))

    def test_set_methods2(self) -> None:
        self.server.add_response(Response(data=FORMS_HTML))
        doc = request(self.server.get_url())
        doc.set_input_by_id("search_box", "asdf")
        self.assertEqual("search_form", doc.get_cached_form().get("id"))

        doc.choose_form(xpath='//form[@id="common_form"]')
        doc.set_input_by_number(0, "asdf")

    def test_set_methods3(self) -> None:
        self.server.add_response(Response(data=FORMS_HTML))
        doc = request(self.server.get_url())
        doc.set_input_by_xpath('//*[@name="gender"]', "2")
        self.assertEqual("common_form", doc.get_cached_form().get("id"))

    def test_html_without_forms(self) -> None:
        self.server.add_response(Response(data=NO_FORM_HTML))
        doc = request(self.server.get_url())
        self.assertRaises(DataNotFound, lambda: doc.form)

    def test_disabled_radio(self) -> None:
        """Test issue #57."""
        self.server.add_response(Response(data=DISABLED_RADIO_HTML))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request())


class TestJustAnotherChunkHtmlForms(BaseTestCase):
    def setUp(self) -> None:
        self.server.reset()

        # Create fake grab instance with fake response
        self.doc = Document(FORMS_HTML)

    def test_set_input_by_xpath_regex(self) -> None:
        html = b"""
            <div><form action="" method="post"><input name="foo" type="text">
            <input name="bar" id="bar" type="text">
        """
        self.server.add_response(Response(data=html))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        doc.set_input_by_xpath('//input[re:test(@id, "^ba")]', "bar-value")
        request(**doc.get_form_request())
        self.assertEqual(self.server.request.data, b"foo=None&bar=bar-value")

    def test_unicode_textarea_form(self) -> None:
        html = """
            <form enctype="multipart/form-data" action=""
                method="post" accept-charset="UTF-8">
                <textarea name="body">Beställa</textarea>
                <input type="submit" name="op" value="Save"/>
            </form>
        """
        self.server.add_response(Response(data=html.encode("utf-8")))
        self.server.add_response(Response())
        doc = request(self.server.get_url())
        request(**doc.get_form_request())
        self.assertTrue("Beställa".encode("utf-8") in self.server.request.data)

    def test_field_disabled(self) -> None:
        html = b"""
            <form>
                <input id="aa" type="radio" name="foo"
                    value="1" disabled="disabled" />
                <input id="bb" type="radio" name="foo"
                    value="2" checked="checked" />
            </form>
        """
        doc = Document(html)
        self.assertEqual({"foo"}, set(doc.form_fields().keys()))

    def test_checkbox_checked_but_disabled(self) -> None:
        html = b"""
            <form>
                <input type="checkbox" name="foo"
                    value="1" checked="checked" disabled="disabled">
            </form>
        """
        doc = Document(html)
        self.assertTrue("foo" not in doc.form_fields())

    def test_checkbox_no_checked(self) -> None:
        html = b"""
            <form>
                <input type="checkbox" name="foo"
                    value="1">
                <input type="checkbox" name="foo"
                    value="2">
            </form>
        """
        doc = Document(html)
        self.assertTrue("foo" not in doc.form_fields())

    def test_checkbox_one_checked(self) -> None:
        html = b"""
            <form>
                <input type="checkbox" name="foo"
                    value="1" checked="checked">
                <input type="checkbox" name="foo"
                    value="2">
            </form>
        """
        doc = Document(html)
        self.assertEqual("1", doc.form_fields()["foo"])

    def test_checkbox_multi_checked(self) -> None:
        html = b"""
            <form>
                <input type="checkbox" name="foo"
                    value="1" checked="checked">
                <input type="checkbox" name="foo"
                    value="2" checked="checked">
            </form>
        """
        doc = Document(html)
        self.assertEqual(["1", "2"], doc.form_fields()["foo"])

    def test_select_disabled(self) -> None:
        html = b"""
            <form>
                <select name="foo" disabled="disabled">
                    <option value="1">1</option>
                </select>
            </form>
        """
        doc = Document(html)
        self.assertTrue("foo" not in doc.form_fields())

    def test_select_not_multiple(self) -> None:
        html = b"""
            <form>
                <select name="foo">
                    <option value="1">1</option>
                </select>
            </form>
        """
        doc = Document(html)
        self.assertEqual("1", doc.form_fields()["foo"])

    def test_select_multiple_no_options(self) -> None:
        html = b"""
            <form>
                <select name="foo" multiple="multiple">
                </select>
            </form>
        """
        doc = Document(html)
        self.assertTrue("foo" not in doc.form_fields())

    def test_select_multiple_one_selected(self) -> None:
        html = b"""
            <form>
                <select name="foo" multiple="multiple">
                    <option value="1">1</option>
                    <option value="2" selected="selected">2</option>
                </select>
            </form>
        """
        doc = Document(html)
        self.assertEqual("2", doc.form_fields()["foo"])

    def test_select_multiple_multi_selected(self) -> None:
        html = b"""
            <form>
                <select name="foo" multiple="multiple">
                    <option value="1" selected="selected">1</option>
                    <option value="2" selected="selected">2</option>
                </select>
            </form>
        """
        doc = Document(html)
        self.assertEqual(["1", "2"], doc.form_fields()["foo"])
