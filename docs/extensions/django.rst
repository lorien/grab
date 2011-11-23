.. _extensions_django:

Shortcut to save response into django FileField
===============================================

If you use Grab in django project then this extension could
be very helpful to you. You can save any network document directly 
to FileField field of any django model.

See example::

    person = Person.objects.filter(unprocessed=True)[0]
    g = Grab()

    # Download image
    g.go(person.avatar_url)

    # Put it into model using `django_file` shortcut
    person.avatar = g.django_file()

    # That's all!
    person.save()


Django Extension API
====================

.. module:: grab.ext.django

.. autoclass:: DjangoExtension

    .. automethod:: django_file
