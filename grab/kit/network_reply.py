"""
I really have no idea how it works ;-)
"""
from PyQt4.QtNetwork import QNetworkReply, QNetworkRequest

from grab.util.py3k_support import *


class KitNetworkReply(QNetworkReply):
    """
    Override QNetworkReply so can save the original data

    Credits:
    * https://code.google.com/p/webscraping/source/browse/webkit.py#154
    * http://gitorious.org/qtwebkit/performance/blobs/master/host-tools/mirror/main.cpp
    """
    def __init__(self, parent, original_reply):
        QNetworkReply.__init__(self, parent)
        self.original_reply = original_reply # reply to proxy
        self.data = '' # contains downloaded data
        self.buffer = '' # contains buffer of data to read
        self.setOpenMode(QNetworkReply.ReadOnly | QNetworkReply.Unbuffered)
        #print dir(reply)
        
        # connect signal from proxy reply
        self.original_reply.metaDataChanged.connect(self.applyMetaData)
        self.original_reply.readyRead.connect(self.readInternal)
        self.original_reply.error.connect(self.error)
        self.original_reply.finished.connect(self.finished)
        self.original_reply.uploadProgress.connect(self.uploadProgress)
        self.original_reply.downloadProgress.connect(self.downloadProgress)

    def __getattribute__(self, attr):
        """Send undefined methods straight through to proxied reply
        """
        # send these attributes through to proxy reply 
        if attr in ('operation', 'request', 'url', 'abort', 'close'):#, 'isSequential'):
            value = self.original_reply.__getattribute__(attr)
        else:
            value = QNetworkReply.__getattribute__(self, attr)
        #print attr, value
        return value
    
    def abort(self):
        pass  # qt requires that this be defined
    
    def isSequential(self):
        return True

    def applyMetaData(self):
        for header in self.original_reply.rawHeaderList():
            self.setRawHeader(header, self.original_reply.rawHeader(header))

        headers = (
            QNetworkRequest.ContentTypeHeader,
            QNetworkRequest.ContentLengthHeader,
            QNetworkRequest.LocationHeader,
            QNetworkRequest.LastModifiedHeader,
            QNetworkRequest.SetCookieHeader,
        )
        for header in headers:
            self.setHeader(header, self.original_reply.header(header))

        attributes = (
            QNetworkRequest.HttpStatusCodeAttribute,
            QNetworkRequest.HttpReasonPhraseAttribute,
            QNetworkRequest.RedirectionTargetAttribute,
            QNetworkRequest.ConnectionEncryptedAttribute,
            QNetworkRequest.CacheLoadControlAttribute,
            QNetworkRequest.CacheSaveControlAttribute,
            QNetworkRequest.SourceIsFromCacheAttribute,

        )
        for attr in attributes:
            self.setAttribute(attr, self.original_reply.attribute(attr))

        # attribute is undefined
        #self.setAttribute(QNetworkRequest.DoNotBufferUploadDataAttribute, self.original_reply.attribute(QNetworkRequest.DoNotBufferUploadDataAttribute))
        self.metaDataChanged.emit()

    def bytesAvailable(self):
        """
        How many bytes in the buffer are available to be read
        """

        return len(self.buffer) + QNetworkReply.bytesAvailable(self)

    def readInternal(self):
        """
        New data available to read
        """

        s = self.original_reply.readAll()
        self.data += s
        self.buffer += s
        self.readyRead.emit()

    def readData(self, size):
        """
        Return up to size bytes from buffer
        """

        size = min(size, len(self.buffer))
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        # py3 hack
        if PY3K:
            return bytes(data)
        else:
            return str(data)
