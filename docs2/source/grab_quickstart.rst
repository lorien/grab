.. _grab_quickstart:

Grab Quick Start
================

In this document we will go through multiple examples of how to use Grab to configure and submit network requests and to process data in network responses.

Let's do something simple, download main page of wikipedia and print some info about response::

    >>> from grab import Grab
    >>> g = Grab()
    >>> g.go('http://en.wikipedia.org')
    <grab.response.Response object at 0x14a1a10>
    >>> g.response.headers['Server']
    'Apache'
    >>> g.response.code
    200
    >>> g.response.body[:30]
    '<!DOCTYPE html>\n<html lang="en'
    >>> g.response.total_time
    0.764033

As you see, after we made a network requests with `go` method, we can access data of response via `grab.resposne` attribute. Also, the `response` objects is a return value of `go` method.

Now let's create more complex request. Let's try to log into pastebin.com::

    >>> g = Grab()
    >>> g.setup(url='http://pastebin.com/login.php',
    ...         post={'user_name': 'foo', 'user_password': 'bar', 'submit_hidden': 'submit_hidden'})
    >>> g.request()
    <grab.response.Response object at 0x14a1a10>
    >>> 'There was an error with your login details' in g.response.body
    True

There is no pastebin user with such credentials, we got response that contains message saying that.

If you want to submit some form, you do not need manually build POST content. You can just download the page with that form, then fill only required fields and then submit the form. Grab will do all necessary stuff automatically. Let's try to log into github::

    >>> g = Grab()
    >>> g.go('https://github.com/login')
    <grab.response.Response object at 0x14a1ae0>
    >>> g.set_input('login', 'foo')
    >>> g.set_input('password', 'bar')
    >>> g.submit()
    <grab.response.Response object at 0x14a1a10>
    >>> 'Incorrect username or password' in g.response.body
    True

See, we filled only two fields, all other form fields were processed automatically. Want to see what's going under the hood? We can pass `make_request=False` option to `submit` method, that allows Grab toconfigure form data that should be submitted but restrict Grab to do any network request::

    ...
    >>> g.submit(make_request=False)
    >>> g.config['post']
    [('commit', 'Sign in'), ('login', 'foo'), ('password', 'bar'), ('authenticity_token', 'DtHmFiYBIWNvFW2B3yg/+NUCJR/O8B2QbgDl00Z8wKw=')]
    
 You can see that Grab automatically assigned values for all form fields that we did not processed explicitly
