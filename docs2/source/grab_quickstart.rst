.. _grab_quickstart:

Grab Quick Start
================

In this document we will go through multiple examples of how to use Grab to configure and submit network requests and to process data in network responses.

Basic Request/Response
----------------------

Let's do something simple: download the main page of wikipedia, and print some info about the response::

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

After we made a network request with the `go` method, we can access data of response via the `grab.response` attribute. Also, a `response` object is returned by the `go` method.

Making a POST request
---------------------

Now let's create a more complex request. Let's try to log into pastebin.com::

    >>> g = Grab()
    >>> g.setup(url='http://pastebin.com/login.php',
    ...         post={'user_name': 'foo', 'user_password': 'bar', 'submit_hidden': 'submit_hidden'})
    >>> g.request()
    <grab.response.Response object at 0x14a1a10>
    >>> 'There was an error with your login details' in g.response.body
    True

There is no pastebin user with such credentials, so we got a response that tells us that information.

In this last example, we used the `post` option to make a POST request. If you pass a dict for the `post` option, then Grab will apply `urllib.urlencode` to the data. If you pass just a string, then Grab will submit it without modification. If you pass a dict mapping unicode strings to unicode values, then Grab will convert all unicode to bytestrings.

Handle Forms
------------

If you want to submit a form, you do not need manually build its POST content. You can just download the page with that form, then fill only the required fields and then submit the form. Grab will do all the necessary stuff automatically. Let's try to log into github::

    >>> g = Grab()
    >>> g.go('https://github.com/login')
    <grab.response.Response object at 0x14a1ae0>
    >>> g.set_input('login', 'foo')
    >>> g.set_input('password', 'bar')
    >>> g.submit()
    <grab.response.Response object at 0x14a1a10>
    >>> 'Incorrect username or password' in g.response.body
    True

Note that we filled only two fields, and all other form fields were processed automatically. Want to see what's going on under the hood? Pass the `make_request=False` option to the `submit` method - this allows Grab to configure form data that should be submitted, but restrict Grab from doing a network request::

    ...
    >>> g.submit(make_request=False)
    >>> g.config['post']
    [('commit', 'Sign in'), ('login', 'foo'), ('password', 'bar'), ('authenticity_token', 'DtHmFiYBIWNvFW2B3yg/+NUCJR/O8B2QbgDl00Z8wKw=')]
    
You can see that Grab automatically assigned values for all form fields that we did not process explicitly.

Stuff that You Have Out of the Box
----------------------------------

By default, Grab mimics the web browser. In most cases you can just focus on the logic of scraping and do not think about annoying things that are done by Grab automatically:

* it stores cookies
* it randomly chooses a User-Agent from some real web browser
* it generates some common HTTP headers like Accept-Charset
* it generates a Referer header
* it follows 301/302 redirects
* it follows meta refresh redirects (disabled by default)
* it automatically detects the charset of the document

Proxy Support
-------------

Now, let's take a quick look at proxy support. There is not much to say, Grab supports all type of proxy (thanks to the power of pycurl). Here is example:

    >>> g = Grab()
    >>> g.setup(proxy='*.*.147.156:1080', proxy_type='socks5', proxy_userpwd='***:***')
    >>> g.go('http://formyip.com/')
    <grab.response.Response object at 0x2adaae0>
    >>> '.147.156' in g.response.body
    True

Response object
---------------

We've talked enough in this tutorial about how to build network requests. Now let's talk about how to process responses. After you make a network request, the main things you can work with are:

* g.response.cookies - cookies
* g.response.headers - HTTP headers of the response
* g.response.code - HTTP code of the response
* g.response.charset - autodetected charset of response (if it is an HTML document)
* g.response.body - the raw content of response (only body, no headers)

Note that g.response.body contains raw content, i.e., if you requested an image you can just save `g.response.body` to the file and that will be OK. For such cases there is a shortcut::

    >>> g.response.save('/path/to/file')

Handling JSON Respone
---------------------

Another shortcut for JSON responses::

    >>> g = Grab()
    >>> g.go(url='https://api.github.com/gitignore/templates')
    <grab.response.Response object at 0x2adaa10>
    >>> g.response.json[:3]
    [u'Actionscript', u'Android', u'AppceleratorTitanium']

Accesssing DOM of HTML Document
-------------------------------

Of course, you can process content of `g.response.body` with regular expressions/lxml/BeautifulSoup/etc but in most of times you'll be happy with the builtin Grab DOM interface. It is too extensive a topic for this tutorial. Just some examples::

    >>> g = Grab()
    >>> g.go('http://www.reddit.com/')
    <grab.response.Response object at 0x2adaa10>
    >>> g.doc.select('//title').text()
    'reddit: the front page of the internet'
    >>> g.doc.select('//p[@class="title"]/a').text_list()[:3]
    ['Ridiculously Photogenic Donkey', 'Reddit, how do I get to a store about 50 minutes away without a car?', 'Subreddit Discovery: Animals!']
    >>> g.doc.select('//p[@class="title"]/a').text()
    'Ridiculously Photogenic Donkey'
    >>> g.doc.select('//p[@class="title"]/a').attr_list('href')[:3]
    ['http://imgur.com/YiekPfv', '/r/AskReddit/comments/1mo3rq/reddit_how_do_i_get_to_a_store_about_50_minutes/', 'http://www.reddit.com/r/AnimalReddits/wiki/faq']
    >>> g.doc.select('//p[@class="title"]/a/@href').text_list()[:3]
    ['http://imgur.com/YiekPfv', '/r/AskReddit/comments/1mo3rq/reddit_how_do_i_get_to_a_store_about_50_minutes/', 'http://www.reddit.com/r/AnimalReddits/wiki/faq']
    >>> g.doc.select('//div[contains(@class, "thing")]').select('.//p[@class="tagline"]/time/@datetime').rex('^(\d{4})-\d{2}-\d{2}').number()
    2013
