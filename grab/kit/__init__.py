"""
Credits:
* https://code.google.com/p/webscraping/source/browse/webkit.py
* https://github.com/jeanphix/Ghost.py/blob/master/ghost/ghost.py
"""
import time 
import sys
from PyQt4.QtCore import QEventLoop, QUrl, QEventLoop, QTimer
from PyQt4.QtGui import QApplication
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtNetwork import (QNetworkAccessManager, QNetworkReply, QNetworkRequest,
                             QNetworkCookieJar)
from lxml.html import fromstring
from grab.selector import Selector
from grab.response import Response
import logging
from grab.kit.network_access_manager import KitNetworkAccessManager
from grab.kit.network_reply import KitNetworkReply
from grab.kit.error import KitError
from grab.kit.network_reply import KitNetworkReply

logger = logging.getLogger('grab.kit')

class KitWebView(QWebView):
    def setApplication(self, app):
        self.app = app

    def closeEvent(self, event):
        self.app.quit()


class KitPage(QWebPage):
    def __init__(self, *args, **kwargs):
        QWebPage.__init__(self)
        self.user_agent = 'QtWebKitWrapper'

    def userAgentForUrl(self, url):
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
    def __init__(self, gui=False):
        self.app = QApplication(sys.argv)

        manager = KitNetworkAccessManager()
        manager.finished.connect(self.reply_handler)

        self.cookie_jar = QNetworkCookieJar()
        manager.setCookieJar(self.cookie_jar)

        self.page = KitPage()
        self.page.setNetworkAccessManager(manager)

        self.view = KitWebView()
        self.view.setPage(self.page)
        self.view.setApplication(self.app)

        if gui:
            self.view.show()

    def get_cookies(self):
        cookies = {}
        for cookie in self.cookie_jar.allCookies():
            cookies[cookie.name().data()] = cookie.value().data()
        return cookies


    def request(self, url, user_agent='Mozilla', timeout=15):
        loop = QEventLoop()
        self.view.loadFinished.connect(loop.quit)
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout * 1000)

        self.page.user_agent = user_agent
        self.view.load(QUrl(url))

        loop.exec_()

        if timer.isActive():
            return self.build_response()
        else:
            raise KitError('Timeout while loading %s' % url)

    def build_response(self):
        response = Response()
        response.head = ''
        response.body = unicode(self.page.mainFrame().toHtml())
        response.code = 200
        response.url = self.view.url(),
        response.parse(charset='utf-8')
        response.cookies = self.get_cookies()
        return response

    def __del__(self):
        self.view.setPage(None)

    def reply_handler(self, reply):
        logger.debug('Loaded %s, length %d' % (reply.url().toString(), len(reply.data)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    br = Kit(gui=False)
    resp = br.request('http://ya.ru/')
    print resp.body[:200]
    print resp.cookies
