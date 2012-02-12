# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
from urlparse import urljoin

from ..base import DataNotFound, GrabMisuseError

class FormExtension(object):
    def extra_reset(self):
        self._lxml_form = None
        self._file_fields = {}

    def choose_form(self, number=None, id=None, name=None, xpath=None):
        """
        Set the default form.
        
        :param number: number of form (starting from zero)
        :param id: value of "id" atrribute
        :param name: value of "name" attribute
        :param xpath: XPath query
        :raises: :class:`DataNotFound` if form not found
        :raises: :class:`GrabMisuseError` if method is called without parameters

        Selected form will be available via `form` atribute of `Grab`
        instance. All form methods will work with defalt form.

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
                self._lxml_form = self.css('form[id="%s"]' % id)
            except IndexError:
                raise DataNotFound("There is no form with id: %s" % id)
        elif name is not None:
            try:
                self._lxml_form = self.css('form[name="%s"]' % name)
            except IndexError:
                raise DataNotFound('There is no form with name: %s' % name)
        elif number is not None:
            try:
                self._lxml_form = self.tree.forms[number]
            except IndexError:
                raise DataNotFound('There is no form with number: %s' % number)
        elif xpath is not None:
            try:
                self._lxml_form = self.xpath(xpath)
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
            forms = [(idx, len(x.fields)) for idx, x in enumerate(self.tree.forms)]
            idx = sorted(forms, key=lambda x: x[1], reverse=True)[0][0]
            self.choose_form(idx)
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

        elem = self.form.inputs[name]

        processed = False
        if getattr(elem, 'type', None) == 'checkbox':
            if isinstance(value, bool):
                elem.checked = value
                processed = True
        
        if not processed:
            # We need to remember origina values of file fields
            # Because lxml will convert UploadContent/UploadFile object to string
            if getattr(elem, 'type', '').lower() == 'file':
                self._file_fields[name] = value
            elem.value = value

    def set_input_by_id(self, _id, value):
        """
        Set the value of form element by its `id` attribute.

        :param _id: id of element
        :param value: value which should be set to element
        """

        elem = self.tree.xpath('//*[@id="%s"]' % _id)[0]
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

        elem = self.tree.xpath(xpath)[0]
        return self.set_input(elem.get('name'), value)


    # TODO:
    # Remove set_input_by_id
    # Remove set_input_by_number
    # New method: set_input_by(id=None, number=None, xpath=None)

    def submit(self, submit_name=None, make_request=True,
               url=None, extra_post=None):
        """
        Submit default form.

        :param submit_name: name of buton which should be "clicked" to
            submit form
        :param make_request: if `False` then grab instance will be
            configured with form post data but request will not be
            performed
        :param url: explicitly specifi form action url
        :param extra_post: additional form data which will override
            data automatically extracted from the form.

        Following input elements are automatically processed:

        * input[type="hidden"] - default value
        * select: value of last option
        * radio - ???
        * checkbox - ???

        Multipart forms are corectly recognized by grab library.

        Example::

            # Assume that we going to some page with some form
            g.go('some url')
            # Fill some fields
            g.set_input('username', 'bob')
            g.set_input('pwd', '123')
            # Submit the form
            g.submit()
            
            # or we can just fill the form
            # and do manu submition
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

        if extra_post:
            post.update(extra_post)

        if self.form.method == 'POST':
            if 'multipart' in self.form.get('enctype', ''):
                for key, obj in self._file_fields.items():
                    post[key] = obj
                self.setup(multipart_post=post.items())
            else:
                self.setup(post=post)
            self.setup(url=action_url)

        else:
            url = action_url.split('?')[0] + '?' + self.urlencode(post.items())
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
                del fields[elem.name]
                continue

            if elem.tag == 'select':
                if not fields[elem.name]:
                    if len(elem.value_options):
                        fields[elem.name] = elem.value_options[-1]
            if getattr(elem, 'type', None) == 'radio':
                if not fields[elem.name]:
                    fields[elem.name] = elem.get('value')
            if getattr(elem, 'type', None) == 'checkbox':
                if not elem.checked:
                    if elem.name is not None:
                        if elem.name in fields:
                            del fields[elem.name]
        return fields
