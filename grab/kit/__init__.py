"""
Credits:
* https://code.google.com/p/webscraping/source/browse/webkit.py
* https://github.com/jeanphix/Ghost.py/blob/master/ghost/ghost.py
"""
#import time
#import sys
from PyQt4.QtCore import QEventLoop, QUrl, QEventLoop, QTimer, QByteArray, QSize
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtNetwork import (QNetworkAccessManager, QNetworkRequest,
                             QNetworkCookieJar, QNetworkCookie)
from lxml.html import fromstring
from grab.selector import Selector
from grab.response import Response
import logging
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit

from grab.kit.network_access_manager import KitNetworkAccessManager
from grab.kit.network_reply import KitNetworkReply
from grab.kit.error import KitError
from grab.tools.encoding import decode_dict
from grab.util.py3k_support import *

logger = logging.getLogger('grab.kit')


class Resource(object):
    def __init__(self, reply):
        self.reply = reply
        self.url = str(reply.url().toString())

        self.status_code = \
            reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if not isinstance(self.status_code, int):
            self.status_code = self.status_code.toInt()[0]
        self.headers = {}
        for header in reply.rawHeaderList():
            self.headers[header.data()] = reply.rawHeader(header).data()


class KitWebView(QWebView):
    def setApplication(self, app):
        self.app = app

    def closeEvent(self, event):
        self.app.quit()

    def sizeHint(self):
        viewport_size = (800, 600)
        return QSize(*viewport_size)


class KitPage(QWebPage):
    def __init__(self, *args, **kwargs):
        QWebPage.__init__(self)
        self.user_agent = 'QtWebKitWrapper'

    def userAgentForUrl(self, url):
        if self.user_agent is None:
            return super(KitPage, self).userAgentForUrl(url)
        else:
            return self.user_agent

    def shouldInterruptJavaScript(self):
        return True

    def javaScriptAlert(self, frame, msg):
        logger.error(u'JavaScript Alert: %s' % unicode(msg))

    def javaScriptConfirm(self, frame, msg):
        logger.error(u'JavaScript Confirm: %s' % unicode(msg))

    def javaScriptPrompt(self, frame, msg, default):
        logger.error(u'JavaScript Prompt: %s' % unicode(msg))

    def javaScriptConsoleMessage(self, msg, line_number, src_id):
        logger.error(u'JavaScript Console Message: %s' % unicode(msg))


class Kit(object):
    _app = None

    def __init__(self, gui=False):
        if not Kit._app:
            Kit._app = QApplication([])

        manager = KitNetworkAccessManager()
        manager.finished.connect(self.network_reply_handler)

        self.cookie_jar = QNetworkCookieJar()
        manager.setCookieJar(self.cookie_jar)

        self.page = KitPage()
        self.page.setNetworkAccessManager(manager)

        self.view = KitWebView()
        self.view.setPage(self.page)
        self.view.setApplication(Kit._app)

        if gui:
            self.view.show()

    def get_cookies(self):
        cookies = {}
        for cookie in self.cookie_jar.allCookies():
            cookies[cookie.name().data()] = cookie.value().data()
        return cookies

    def request(self, url, user_agent='Mozilla', cookies=None, timeout=15,
                method='get', data=None, headers=None):
        if cookies is None:
            cookies = {}
        if headers is None:
            headers = {}
        url_info = urlsplit(url)

        self.resource_list = []
        loop = QEventLoop()
        self.view.loadFinished.connect(loop.quit)

        # Timeout
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout * 1000)

        # User-Agent
        self.page.user_agent = user_agent

        # Cookies
        cookie_obj_list = []
        for name, value in cookies.items():
            domain = ('.' + url_info.netloc).split(':')[0]
            #print 'CREATE COOKIE %s=%s' % (name, value)
            #print 'DOMAIN = %s' % domain
            cookie_obj = QNetworkCookie(name, value)
            cookie_obj.setDomain(domain)
            cookie_obj_list.append(cookie_obj)
        self.cookie_jar.setAllCookies(cookie_obj_list)

        # Method
        method_obj = getattr(QNetworkAccessManager, '%sOperation'
                             % method.capitalize())

        # Ensure that Content-Type is correct if method is post
        if method == 'post':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

        # Post data
        if data is None:
            data = QByteArray()

        # Request object
        request_obj = QNetworkRequest(QUrl(url))

        # Headers
        for name, value in headers.items():
            request_obj.setRawHeader(name, value)

        # Make a request
        self.view.load(request_obj, method_obj, data)

        loop.exec_()

        if timer.isActive():
            request_resource = None
            url = str(self.page.mainFrame().url().toString()).rstrip('/')
            for res in self.resource_list:
                if url == res.url or url == res.url.rstrip('/'):
                    request_resource = res
                    break
            if request_resource:
                return self.build_response(request_resource)
            else:
                raise KitError('Request was successful but it is not possible'
                               ' to associate the request to one of received'
                               ' responses')
        else:
            raise KitError('Timeout while loading %s' % url)

    def build_response(self, resource):
        response = Response()
        response.head = ''
        response.code = resource.status_code

        runtime_body = self.page.mainFrame().toHtml()
        body = resource.reply.data
        url = resource.reply.url().toString()
        headers = resource.headers
        cookies = self.get_cookies()

        # py3 hack
        if PY3K:
            if isinstance(body, QByteArray):
                body = body.data()
            headers = decode_dict(headers)
            cookies = decode_dict(cookies)
        else:
            runtime_body = unicode(runtime_body)
            body = str(body)
            url = str(url)

        response.runtime_body = runtime_body.encode('utf-8')
        response.body = body
        response.url = url
        response.parse(charset='utf-8')
        response.headers = headers
        response.cookies = cookies

        return response

    def __del__(self):
        self.view.setPage(None)

    def network_reply_handler(self, reply):
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status_code:
            if not isinstance(status_code, int):
                status_code = status_code.toInt()[0]
            logger.debug('Resource loaded: %s [%d]' % (reply.url().toString(),
                                                       status_code))
            self.resource_list.append(Resource(reply))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    br = Kit(gui=False)
    #resp = br.request('http://httpbin.org/post', method='post', cookies={'foo': 'bar'},
                      #data='foo=bar')
    #print(resp.body)
    resp = br.request('http://ya.ru/')
    print(unicode(br.page.mainFrame().documentElement().findFirst('title').toPlainText()))
