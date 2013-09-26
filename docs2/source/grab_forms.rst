.. _grab_forms:

Form Processing
===============

Grab helps you to process web forms. It automatically fills all input fields that has default values and let you focus only on subset of fields. The typical workflow is::

* request a page
* fill input fields with `set_input` method
* submit the form with `submit` method

When you are using `set_input` you just specify name of input and the value and Grab automatically find the form that has the input with such name. When you call `submit` the automatically choosed form is submitted (the form that have bigeest number of fields). You can explicitly choose the form with `choose_form` method.

Let's see the simple example of using form features::

    >>> g = Grab()
    >>> g.go('http://ya.ru/')
    >>> g.set_input('text', 'grab lib')
    >>> g.submit()
    >>> g.doc.select('//a[@class="b-serp-item__title-link"]/@href').text()
    'http://grablib.org/'

The form that has been choosed automatically is available at `grab.form` attribute.

To specify input values you can use `set_input`, `set_input_by_id` and `set_input_by_xpath` methods.
