import sys

import six

from .curl import CurlTransport, build_grab_exception
from .. import error

"""
Implementation of pycurl's "easy" interface that uses pycurl's multi interface + gevent.
Based on Tornado curl_httpclient.py
"""

import asyncio
import weakref

import pycurl


class AioCurlMulti:
    """Integrate Curl's Multi interface into asyncio loop."""

    def __init__(self, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self._timeout = None
        self._obj = pycurl.CurlMulti()

        self_ref = weakref.ref(self)
        self._obj.setopt(pycurl.M_TIMERFUNCTION, lambda msecs: AioCurlMulti._set_timeout(self_ref(), msecs))
        self._obj.setopt(pycurl.M_SOCKETFUNCTION, lambda event, fd, multi, data: AioCurlMulti._set_socket(self_ref(), event, fd, multi, data))

    @staticmethod
    def _set_timeout(self, msecs):
        """Called by libcurl to schedule a timeout."""
        if self._timeout is not None:
            self._timeout.cancel()
            self._timeout = None
        if msecs == -1:
            return

        self_ref = weakref.ref(self)
        self._timeout = self.loop.call_later(msecs / 1000, AioCurlMulti._handle_timeout, self_ref())

    def add_handle(self, curl):
        self._obj.add_handle(curl)
        self._set_timeout(self, 0)

    def remove_handle(self, curl):
        self._obj.remove_handle(curl)

    def _set_socket(self, event, fd, multi, data):
        """Called by libcurl when it wants to change the file descriptors it cares about."""
        if event & pycurl.POLL_IN:
            self.loop.add_reader(fd, self._handle_events, pycurl.CSELECT_IN, fd)
        else:
            self.loop.remove_reader(fd)
        if event & pycurl.POLL_OUT:
            self.loop.add_writer(fd, self._handle_events, pycurl.CSELECT_OUT, fd)
        else:
            self.loop.remove_writer(fd)

    @staticmethod
    def _handle_timeout(self):
        """Called by IOLoop when the requested timeout has passed."""
        if self is None:
            return

        if self._timeout is not None:
            self._timeout.cancel()
            self._timeout = None
        while True:
            try:
                ret, num_handles = self._obj.socket_action(pycurl.SOCKET_TIMEOUT, 0)
            except pycurl.error as e:
                ret = e.args[0]
            if ret != pycurl.E_CALL_MULTI_PERFORM:
                break
        self._finish_pending_requests()

        # In theory, we shouldn't have to do this because curl will
        # call _set_timeout whenever the timeout changes.  However,
        # sometimes after _handle_timeout we will need to reschedule
        # immediately even though nothing has changed from curl's
        # perspective.  This is because when socket_action is
        # called with SOCKET_TIMEOUT, libcurl decides internally which
        # timeouts need to be processed by using a monotonic clock
        # (where available) while tornado uses python's time.time()
        # to decide when timeouts have occurred.  When those clocks
        # disagree on elapsed time (as they will whenever there is an
        # NTP adjustment), tornado might call _handle_timeout before
        # libcurl is ready.  After each timeout, resync the scheduled
        # timeout with libcurl's current state.
        new_timeout = self._obj.timeout()
        if new_timeout >= 0:
            self._set_timeout(self, new_timeout)

    def _handle_events(self, action, fd):
        while True:
            try:
                ret, num_handles = self._obj.socket_action(fd, action)
            except pycurl.error as e:
                ret = e.args[0]
            if ret != pycurl.E_CALL_MULTI_PERFORM:
                break
        self._finish_pending_requests()

    def _finish_pending_requests(self):
        """Process any requests that were completed by the lastcall to multi.socket_action."""
        while True:
            num_q, ok_list, err_list = self._obj.info_read()
            for curl in ok_list:
                curl.waiter.set_result(None)
            for curl, errnum, errmsg in err_list:
                curl.waiter.set_exception(pycurl.error(errnum, errmsg))
            if num_q == 0:
                break


class AioCurl:
    def __init__(self, multi):
        self.loop = multi.loop
        self._multi = multi

        self._obj = pycurl.Curl()

    def __getattr__(self, item):
        return getattr(self._obj, item)

    async def perform(self):
        assert getattr(self._obj, 'waiter', None) is None, 'This curl object is already in use'
        waiter = self._obj.waiter = self.loop.create_future()
        try:
            self._multi.add_handle(self._obj)
            try:
                return await waiter
            finally:
                self._multi.remove_handle(self._obj)
        finally:
            del self._obj.waiter


class AioCurlTransport(CurlTransport):
    def __init__(self, loop=None):
        super().__init__()
        self.curl_multi = AioCurlMulti(loop=loop)
        self.curl = AioCurl(self.curl_multi)

    async def request(self):                          
        try:                                
            await self.curl.perform()
        except pycurl.error as ex:
            new_ex = build_grab_exception(ex, self.curl)     
            if new_ex:                  
                raise new_ex # pylint: disable=raising-bad-type
        except Exception as ex: # pylint: disable=broad-except     
            six.reraise(error.GrabInternalError, error.GrabInternalError(ex),
                        sys.exc_info()[2])
        finally:
            self.curl.grab_callback_interrupted = False

