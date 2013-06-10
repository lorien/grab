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
import logging

logger = logging.getLogger('webkit_wrapper')

class KitError(Exception):
    pass


class Response(object):
    def __init__(self, body, url, cookie_jar):
        self.body = body
        self.url = url
        self.doc = Selector(fromstring(body)) 
        self.cookie_jar = cookie_jar
        self.cookies = {}
        for cookie in self.cookie_jar.allCookies():
            self.cookies[cookie.name().data()] = cookie.value().data()

class KitNetworkAccessManager(QNetworkAccessManager):
    def __init__(self, forbidden_extensions=[]):
        QNetworkAccessManager.__init__(self)
        self.forbidden_extensions = forbidden_extensions

    def setupCache(self, size=100 * 1024 * 1024, location='/tmp/.webkit_wrapper'):
        QDesktopServices.storageLocation(QDesktopServices.CacheLocation)
        cache = QNetworkDiskCache()
        cache.setCacheDirectory(location)
        cache.setMaximumCacheSize(size)
        self.setCache(cache)

    def setupProxy(self, proxy, proxy_userpwd=None, proxy_type='http'):
        if proxy_userpwd:
            username, password = proxy_userpwd.split(':', 1)
        else:
            username, password = '', ''
        host, port = proxy.split(':', 1)
        if proxy_type == 'http':
            proxy_type_obj = QNetworkProxy.HttpProxy
        elif proxy_type == 'socks5':
            proxy_type_obj = QNetworkProxy.Socks5Proxy
        else:
            raise KitError('Unknown proxy type: %s' % proxy_type)
        proxy_obj = QNetworkProxy(proxy_type_obj, host, int(port), username, password)
        self.setProxy(self, proxy_obj)

    def createRequest(self, operation, request, data):
        if operation == self.GetOperation:
            if not self.is_request_allowed(request):
                request.setUrl(QUrl('forbidden://localhost/'))
            else:
                logger.debug(u'Requesting URL: %s' % request.url().toString())
        
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.PreferCache)
        reply = QNetworkAccessManager.createRequest(self, operation, request, data)
        reply.error.connect(self.catch_error)
        reply = NetworkReply(self, reply)
        
        # add Base-Url header, then we can get it from QWebView
        #if isinstance(request.originatingObject(), QWebFrame):
            #try:
                #reply.setRawHeader(QByteArray('Base-Url'), QByteArray('').append(request.originatingObject().page().mainFrame().baseUrl().toString()))
            #except Exception, e:
                #common.logger.debug(e)

        return reply

    def is_request_allowed(self, request):
        #url = unicode(request.url().toString())
        path = unicode(request.url().path())
        ext = ''
        if path:
            if '.' in path:
                ext = path.rsplit('.', 1)[-1].lower()

        if self.forbidden_extensions and ext in self.forbidden_extensions:
            logger.debug('Url %s is not allowed because ext %s is forbiddend' % url, ext)
            return False

        return True


    def catch_error(self, eid):
        """Interpret the HTTP error ID received
        """

        if eid not in (5, 301):
            errors = {
                0 : 'no error condition. Note: When the HTTP protocol returns a redirect no error will be reported. You can check if there is a redirect with the QNetworkRequest::RedirectionTargetAttribute attribute.',

                1 : 'the remote server refused the connection (the server is not accepting requests)',
                2 : 'the remote server closed the connection prematurely, before the entire reply was received and processed',
                3 : 'the remote host name was not found (invalid hostname)',
                4 : 'the connection to the remote server timed out',
                5 : 'the operation was canceled via calls to abort() or close() before it was finished.',
                6 : 'the SSL/TLS handshake failed and the encrypted channel could not be established. The sslErrors() signal should have been emitted.',
                7 : 'the connection was broken due to disconnection from the network, however the system has initiated roaming to another access point. The request should be resubmitted and will be processed as soon as the connection is re-established.',
                101 : 'the connection to the proxy server was refused (the proxy server is not accepting requests)',
                102 : 'the proxy server closed the connection prematurely, before the entire reply was received and processed',
                103 : 'the proxy host name was not found (invalid proxy hostname)',
                104 : 'the connection to the proxy timed out or the proxy did not reply in time to the request sent',
                105 : 'the proxy requires authentication in order to honour the request but did not accept any credentials offered (if any)',
                201 : 'the access to the remote content was denied (similar to HTTP error 401)',
                202 : 'the operation requested on the remote content is not permitted',
                203 : 'the remote content was not found at the server (similar to HTTP error 404)',
                204 : 'the remote server requires authentication to serve the content but the credentials provided were not accepted (if any)',
                205 : 'the request needed to be sent again, but this failed for example because the upload data could not be read a second time.',
                301 : 'the Network Access API cannot honor the request because the protocol is not known',
                302 : 'the requested operation is invalid for this protocol',
                99 : 'an unknown network-related error was detected',
                199 : 'an unknown proxy-related error was detected',
                299 : 'an unknown error related to the remote content was detected',
                399 : 'a breakdown in protocol was detected (parsing error, invalid or unexpected responses, etc.)',
            }
            logger.error('Error %d: %s (%s)' % (eid, errors.get(eid, 'unknown error'), self.sender().url().toString()))


class NetworkReply(QNetworkReply):
    """Override QNetworkReply so can save the original data
    """
    def __init__(self, parent, reply):
        QNetworkReply.__init__(self, parent)
        self.reply = reply # reply to proxy
        self.data = '' # contains downloaded data
        self.buffer = '' # contains buffer of data to read
        self.setOpenMode(QNetworkReply.ReadOnly | QNetworkReply.Unbuffered)
        #print dir(reply)
        
        # connect signal from proxy reply
        reply.metaDataChanged.connect(self.applyMetaData)
        reply.readyRead.connect(self.readInternal)
        reply.finished.connect(self.finished)
        reply.uploadProgress.connect(self.uploadProgress)
        reply.downloadProgress.connect(self.downloadProgress)

    
    def __getattribute__(self, attr):
        """Send undefined methods straight through to proxied reply
        """
        # send these attributes through to proxy reply 
        if attr in ('operation', 'request', 'url', 'abort', 'close'):#, 'isSequential'):
            value = self.reply.__getattribute__(attr)
        else:
            value = QNetworkReply.__getattribute__(self, attr)
        #print attr, value
        return value
    
    def abort(self):
        pass # qt requires that this be defined
    
    def isSequential(self):
        return True

    def applyMetaData(self):
        for header in self.reply.rawHeaderList():
            self.setRawHeader(header, self.reply.rawHeader(header))

        self.setHeader(QNetworkRequest.ContentTypeHeader, self.reply.header(QNetworkRequest.ContentTypeHeader))
        self.setHeader(QNetworkRequest.ContentLengthHeader, self.reply.header(QNetworkRequest.ContentLengthHeader))
        self.setHeader(QNetworkRequest.LocationHeader, self.reply.header(QNetworkRequest.LocationHeader))
        self.setHeader(QNetworkRequest.LastModifiedHeader, self.reply.header(QNetworkRequest.LastModifiedHeader))
        self.setHeader(QNetworkRequest.SetCookieHeader, self.reply.header(QNetworkRequest.SetCookieHeader))

        self.setAttribute(QNetworkRequest.HttpStatusCodeAttribute, self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute))
        self.setAttribute(QNetworkRequest.HttpReasonPhraseAttribute, self.reply.attribute(QNetworkRequest.HttpReasonPhraseAttribute))
        self.setAttribute(QNetworkRequest.RedirectionTargetAttribute, self.reply.attribute(QNetworkRequest.RedirectionTargetAttribute))
        self.setAttribute(QNetworkRequest.ConnectionEncryptedAttribute, self.reply.attribute(QNetworkRequest.ConnectionEncryptedAttribute))
        self.setAttribute(QNetworkRequest.CacheLoadControlAttribute, self.reply.attribute(QNetworkRequest.CacheLoadControlAttribute))
        self.setAttribute(QNetworkRequest.CacheSaveControlAttribute, self.reply.attribute(QNetworkRequest.CacheSaveControlAttribute))
        self.setAttribute(QNetworkRequest.SourceIsFromCacheAttribute, self.reply.attribute(QNetworkRequest.SourceIsFromCacheAttribute))
        # attribute is undefined
        #self.setAttribute(QNetworkRequest.DoNotBufferUploadDataAttribute, self.reply.attribute(QNetworkRequest.DoNotBufferUploadDataAttribute))
        self.metaDataChanged.emit()

    def bytesAvailable(self):
        """How many bytes in the buffer are available to be read
        """
        return len(self.buffer) + QNetworkReply.bytesAvailable(self)

    def readInternal(self):
        """New data available to read
        """
        s = self.reply.readAll()
        self.data += s
        self.buffer += s
        self.readyRead.emit()

    def readData(self, size):
        """Return up to size bytes from buffer
        """
        size = min(size, len(self.buffer))
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return str(data)


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

        #manager = QNetworkAccessManager()
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
            res = Response(
                body=unicode(self.page.mainFrame().toHtml()),
                url=self.view.url(),
                cookie_jar=self.cookie_jar,
            )
            return res
        else:
            raise KitError('Timeout while loading %s' % url)

    def __del__(self):
        self.view.setPage(None)

    def reply_handler(self, reply):
        logger.debug('Loaded %s, length %d' % (reply.url().toString(), len(reply.data)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    br = Kit(gui=False)
    resp = br.request('http://ya.ru/')
    print resp.doc.select('//title').text()
    print resp.cookies
