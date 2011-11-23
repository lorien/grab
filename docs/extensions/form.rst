.. _extensions_form:

Grab Form Extension
===================

The usual way of working with forms::

    g = Grab()
    g.go('some page with form')

    # Choose the third form
    # Form numerations starts from zero
    g.choose_form(2)

    g.set_input('username', 'foo')
    g.set_input('password', 'foo')
    g.submit()

BTW, the call to `choose_form` is optional. When you tries to work
with form and no form is selected then Grab selects the form
automatially. It does smart selection: the form with most bigger
number of visible fields are selected.

The selected form is available via `form` attribute of Grab instance.
Under the hood Grab uses lxml to process forms. So any form or any
input element is just a `lxml.etree.ElementTree` object.

To learn more about form processing in lxml read this: URL TO LXML DOCUMENTATION

Form Extension API
------------------

.. module:: grab.ext.form

.. autoclass:: FormExtension

    To start working with form you should select it

    .. automethod:: choose_form

    .. autoattribute:: form

    .. automethod:: set_input
    .. automethod:: set_input_by_id
    .. automethod:: set_input_by_number
    .. automethod:: submit
