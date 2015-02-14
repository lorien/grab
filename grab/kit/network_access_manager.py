import logging
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt4.QtWebKit import QWebFrame
from PyQt4.QtCore import QByteArray

from grab.kit.const import NETWORK_ERROR
from grab.kit.network_reply import KitNetworkReply
from grab.kit.error import KitError
from grab.util.py3k_support import *

logger = logging.getLogger('grab.kit.network_access_manager')


class KitNetworkAccessManager(QNetworkAccessManager):
    def __init__(self, forbidden_extensions=None):
        if forbidden_extensions is None:
            forbidden_extensions = []
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
                logger.debug(u'Querying URL: %s' % request.url().toString())
        
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute,
                             QNetworkRequest.PreferCache)
        reply = QNetworkAccessManager.createRequest(self, operation, request, data)
        reply.error.connect(self.catch_error)
        reply = KitNetworkReply(self, reply)
        
        # add Base-Url header, then we can get it from QWebView
        # WTF?
        if isinstance(request.originatingObject(), QWebFrame):
            try:
                reply.setRawHeader(
                    QByteArray('Base-Url'),
                    QByteArray('').append(request.originatingObject().page()
                                          .mainFrame().baseUrl().toString()))
            except Exception as e:
                logger.debug(e)

        return reply

    def is_request_allowed(self, request):
        #url = unicode(request.url().toString())
        path = unicode(request.url().path())
        ext = ''
        if path:
            if '.' in path:
                ext = path.rsplit('.', 1)[-1].lower()

        if self.forbidden_extensions and ext in self.forbidden_extensions:
            logger.debug('Url %s is not allowed because ext %s is forbidden'
                         % url, ext)
            return False

        return True

    def catch_error(self, eid):
        """
        Interpret the HTTP error ID received
        """

        if eid not in (5, 301):
            logger.error('Error %d: %s (%s)'
                         % (eid, NETWORK_ERROR.get(eid, 'unknown error'),
                            self.sender().url().toString()))
