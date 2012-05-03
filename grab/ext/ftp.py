"""
This module works only with curl transport.
"""
# Copyright: 2011, Grigoriy Petukhov
# Author: Grigoriy Petukhov (http://lorien.name)
# License: BSD
from __future__ import absolute_import
import os.path
import os

class FTPExtension(object):
    def ftp_upload_file(self, server, local_path, remote_path, userpwd=None,
                        make_request=True):
        import pycurl

        if userpwd:
            self.setup(userpwd=userpwd)#config['userpwd'] = userpwd
            #g.curl.setopt(pycurl.USERPWD, userpwd)

        # TODO: Reset UPLOAD in grab.reset()
        #self.transport.curl.setopt(pycurl.UPLOAD, 1)
        self.setup(method='upload')

        url = 'ftp://%s%s' % (server, remote_path)
        self.setup(url=url)
        #g.curl.setopt(pycurl.URL, url)

        fp = open(local_path)
        # TODO: Reset READDATA in grab.reset()

        # low level settings
        self.transport.curl.setopt(pycurl.READDATA, fp)
        self.transport.curl.setopt(pycurl.INFILESIZE, os.path.getsize(local_path))
        self.transport.curl.setopt(pycurl.FTP_CREATE_MISSING_DIRS, 1)

        # TODO:
        # http://www.saltycrane.com/blog/2011/10/using-curl-ftp-took-3-minutes-4-byte-file-epsv/
        self.transport.curl.setopt(pycurl.FTP_USE_EPSV, 0)

        if make_request:
            self.request()

    def ftp_upload_directory(self, server, local_dir, remote_dir, userpwd=None):
        for root, dirs, files in os.walk(local_dir):
            for fname in files:
                local_path = os.path.join(root, fname)
                rel_path = local_path[len(local_dir):].lstrip('/') 
                self.ftp_upload_file(
                    server,
                    os.path.join(root, fname),
                    remote_dir + rel_path,
                    userpwd=userpwd)
                print local_path, '-->', remote_dir + rel_path
            #for _dir in dirs:
                #shutil.rmtree(os.path.join(root, _dir))
