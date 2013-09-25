.. _grab_quickstart:

Grab Quick Start
================

In this document we will go through multiple examples of how to use Grab to configure and submit network requests and to process data in network responses.

Basic Request/Response
----------------------

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

After we made a network requests with `go` method, we can access data of response via `grab.response` attribute. Also, the `response` objects is returned by `go` method.

Making a POST request
---------------------

Now let's create more complex request. Let's try to log into pastebin.com::

    >>> g = Grab()
    >>> g.setup(url='http://pastebin.com/login.php',
    ...         post={'user_name': 'foo', 'user_password': 'bar', 'submit_hidden': 'submit_hidden'})
    >>> g.request()
    <grab.response.Response object at 0x14a1a10>
    >>> 'There was an error with your login details' in g.response.body
    True

There is no pastebin user with such credentials, we got response that contains message saying that.

In last example we used `post` options to make POST request. If you pass dict to `post` option the Grab will applay `urllib.urlencode` to the data, if you pass just a string data then Grab will submit it without any modification. If you pass unicode-string of dict with unicode values then Grab will convert all unicode to byte strings.

Handle Forms
------------

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
    
 You can see that Grab automatically assigned values for all form fields that we did not processed explicitly.

Stuff that You Have Out of the Box
----------------------------------

By default, Grab mimics the web browser. In most of cases you can just focus on logic of scraping and do not think about annoying things that is done by Grab automatically:

* it remember cookies
* it generates random User-Agent of some real web browser
* it generates some common HTTP headers like Accepth-Charset
* it generates Referer
* it follows 301/302 redirects
* it follows meta refresh redirects (disabled by default)
* it automatically detect the charset of the document

Proxy Support
-------------

Now, let's take a quick look on proxy support. There is no much to say, Grab supports all type of proxy (thanks to pycurl power). Here is example:

    >>> g = Grab()
    >>> g.setup(proxy='*.*.147.156:1080', proxy_type='socks5', proxy_userpwd='***:***')
    >>> g.go('http://formyip.com/')
    <grab.response.Response object at 0x2adaae0>
    >>> '.147.156' in g.response.body
    True

Response object
---------------

We talked enough in this tutorial about how to build network requests. Now let's talk about how to process responses. After you made a network request the main things you can work with are:

* g.response.cookies - cookies
* g.response.headers - HTTP headers of the response
* g.response.code - HTTP code of the response
* g.response.charset - autodetected charset of response(if it is an HTML document)
* g.response.body - the raw content of response (only body, no headers)

Note that g.response.body contains raw content i.e. if you requested image you can just save `g.response.body` to the file and that will be OK. For such case there is a shortcut::

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

Of course, you can process content of `g.response.body` with regular expressions/lxml/BeautifulSoup/etc but in most of times you'll be happy with builtin Grab DOM interface. It is too extensive topic for this tutorial. Just some examples::

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
