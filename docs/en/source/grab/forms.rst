.. _grab_forms:

Form Processing
===============

Grab can help you process web forms. It can automatically fill all input fields
that have default values, letting you fill only fields you need.
The typical workflow is::

* request a page
* fill input fields with `set_input` method
* submit the form with `submit` method

When you are using `set_input` you just specify the name of an input and the value, and
Grab automatically finds the form field containing the input with that name. When you
call `submit`, the automatically-chosen form is submitted (the form that has
the largest number of fields). You can also explicitly choose the form with
the `choose_form` method.

Let's look at a simple example of how to use these form features::

    >>> g = Grab()
    >>> g.go('http://ya.ru/')
    >>> g.set_input('text', 'grab lib')
    >>> g.submit()
    >>> g.doc.select('//a[@class="b-serp-item__title-link"]/@href').text()
    'http://grablib.org/'

The form that has been chosen automatically is available in the `grab.form` attribute.

To specify input values you can use `set_input`, `set_input_by_id` and `set_input_by_xpath` methods.

