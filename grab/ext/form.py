# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from grab.error import DataNotFound, GrabMisuseError
from grab.tools.http import smart_urlencode

# TODO: refactor this hell


class FormExtension(object):
    __slots__ = ()
    # SLOTS: _lxml_form, _file_fields

    def extra_reset(self):
        self._lxml_form = None
        self._file_fields = {}

    def choose_form(self, number=None, id=None, name=None, xpath=None):
        """
        Set the default form.
        
        :param number: number of form (starting from zero)
        :param id: value of "id" attribute
        :param name: value of "name" attribute
        :param xpath: XPath query
        :raises: :class:`DataNotFound` if form not found
        :raises: :class:`GrabMisuseError` if method is called without parameters

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

        if id is not None:
            try:
                self._lxml_form = self.doc('//form[@id="%s"]' % id).node()
            except IndexError:
                raise DataNotFound("There is no form with id: %s" % id)
        elif name is not None:
            try:
                self._lxml_form = self.doc('//form[@name="%s"]' % name).node()
            except IndexError:
                raise DataNotFound('There is no form with name: %s' % name)
        elif number is not None:
            try:
                self._lxml_form = self.doc.tree.forms[number]
            except IndexError:
                raise DataNotFound('There is no form with number: %s' % number)
        elif xpath is not None:
            try:
                self._lxml_form = self.doc.select(xpath).node()
            except IndexError:
                raise DataNotFound('Could not find form with xpath: %s' % xpath)
        else:
            raise GrabMisuseError('choose_form methods requires one of '
                                  '[number, id, name, xpath] arguments')
                
    @property
    def form(self):
        """
        This attribute points to default form.

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
            forms = [(idx, len(list(x.fields)))
                     for idx, x in enumerate(self.doc.tree.forms)]
            if len(forms):
                idx = sorted(forms, key=lambda x: x[1], reverse=True)[0][0]
                self.choose_form(idx)
            else:
                raise DataNotFound('Response does not contains any form')
        return self._lxml_form

    def set_input(self, name, value):
        """
        Set the value of form element by its `name` attribute.

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
        if getattr(elem, 'type', None) == 'checkbox':
            if isinstance(value, bool):
                elem.checked = value
                processed = True
        
        if not processed:
            # We need to remember original values of file fields
            # Because lxml will convert UploadContent/UploadFile object to
            # string
            if getattr(elem, 'type', '').lower() == 'file':
                self._file_fields[name] = value
            elem.value = value

    def set_input_by_id(self, _id, value):
        """
        Set the value of form element by its `id` attribute.

        :param _id: id of element
        :param value: value which should be set to element
        """

        xpath = './/*[@id="%s"]' % _id
        if self._lxml_form is None:
            self.choose_form_by_element(xpath)
        elem = self.form.xpath(xpath)[0]
        return self.set_input(elem.get('name'), value)

    def set_input_by_number(self, number, value):
        """
        Set the value of form element by its number in the form

        :param number: number of element
        :param value: value which should be set to element
        """

        elem = self.form.xpath('.//input[@type="text"]')[number]
        return self.set_input(elem.get('name'), value)

    def set_input_by_xpath(self, xpath, value):
        """
        Set the value of form element by xpath

        :param xpath: xpath path
        :param value: value which should be set to element
        """

        elem = self.doc.tree.xpath(xpath)[0]

        if self._lxml_form is None:
            # Explicitly set the default form 
            # which contains found element
            parent = elem
            while True:
                parent = parent.getparent()
                if parent.tag == 'form':
                    self._lxml_form = parent
                    break

        return self.set_input(elem.get('name'), value)

    # TODO:
    # Remove set_input_by_id
    # Remove set_input_by_number
    # New method: set_input_by(id=None, number=None, xpath=None)

    def submit(self, submit_name=None, make_request=True,
               url=None, extra_post=None):
        """
        Submit default form.

        :param submit_name: name of button which should be "clicked" to
            submit form
        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed
        :param url: explicitly specify form action url
        :param extra_post: (dict or list of pairs) additional form data which
            will override data automatically extracted from the form.

        Following input elements are automatically processed:

        * input[type="hidden"] - default value
        * select: value of last option
        * radio - ???
        * checkbox - ???

        Multipart forms are correctly recognized by grab library.

        Example::

            # Assume that we going to some page with some form
            g.go('some url')
            # Fill some fields
            g.set_input('username', 'bob')
            g.set_input('pwd', '123')
            # Submit the form
            g.submit()
            
            # or we can just fill the form
            # and do manual submission
            g.set_input('foo', 'bar')
            g.submit(make_request=False)
            g.request()

            # for multipart forms we can specify files
            from grab import UploadFile
            g.set_input('img', UploadFile('/path/to/image.png'))
            g.submit()
        """

        # TODO: add .x and .y items
        # if submit element is image

        post = self.form_fields()
        submit_control = None

        # Build list of submit buttons which have a name
        submit_controls = {}
        for elem in self.form.inputs:
            if (elem.tag == 'input' and elem.type == 'submit' and
                elem.get('name') is not None):
                submit_controls[elem.name] = elem

        # All this code need only for one reason:
        # to not send multiple submit keys in form data
        # in real life only this key is submitted whose button
        # was pressed
        if len(submit_controls):
            # If name of submit control is not given then
            # use the name of first submit control
            if submit_name is None or not submit_name in submit_controls:
                controls = sorted(submit_controls.values(), key=lambda x: x.name)
                submit_name = controls[0].name

            # Form data should contain only one submit control
            for name in submit_controls:
                if name != submit_name:
                    if name in post:
                        del post[name]

        if url:
            action_url = urljoin(self.response.url, url)
        else:
            action_url = urljoin(self.response.url, self.form.action)

        # Values from `extra_post` should override values in form
        # `extra_post` allows multiple value of one key

        # Process saved values of file fields
        if self.form.method == 'POST':
            if 'multipart' in self.form.get('enctype', ''):
                for key, obj in self._file_fields.items():
                    post[key] = obj

        post_items = list(post.items())
        del post

        if extra_post:
            if isinstance(extra_post, dict):
                extra_post_items = extra_post.items()
            else:
                extra_post_items = extra_post

            # Drop existing post items with such key
            keys_to_drop = set([x for x, y in extra_post_items])
            for key in keys_to_drop:
                post_items = [(x, y) for x, y in post_items if x != key]

            for key, value in extra_post_items:
                post_items.append((key, value))

        if self.form.method == 'POST':
            if 'multipart' in self.form.get('enctype', ''):
                self.setup(multipart_post=post_items)
            else:
                self.setup(post=post_items)
            self.setup(url=action_url)

        else:
            url = action_url.split('?')[0] + '?' + smart_urlencode(post_items)
            self.setup(url=url)

        if make_request:
            return self.request()
        else:
            return None

    def form_fields(self):
        """
        Return fields of default form.

        Fill some fields with reasonable values.
        """

        fields = dict(self.form.fields)
        for elem in self.form.inputs:
            # Ignore elements without name
            if not elem.get('name'):
                continue

            # Do not submit disabled fields
            # http://www.w3.org/TR/html4/interact/forms.html#h-17.12
            if elem.get('disabled'):
                if elem.name in fields:
                    del fields[elem.name]

            elif elem.tag == 'select':
                if fields[elem.name] is None:
                    if len(elem.value_options):
                        fields[elem.name] = elem.value_options[0]

            elif getattr(elem, 'type', None) == 'radio':
                if fields[elem.name] is None:
                    fields[elem.name] = elem.get('value')

            elif getattr(elem, 'type', None) == 'checkbox':
                if not elem.checked:
                    if elem.name is not None:
                        if elem.name in fields:
                            del fields[elem.name]

        return fields

    def choose_form_by_element(self, xpath):
        forms = self.doc.tree.xpath('//form')
        found_form = None
        for form in forms:
            if len(form.xpath(xpath)):
                found_form = form
                break
        self._lxml_form = found_form if found_form is not None else forms[0]
