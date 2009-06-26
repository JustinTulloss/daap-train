# Copyright (c) 2009 Harmonize, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from webob import Request, Response, exc
from threading import Thread

try:
    from pybonjour import (
        DNSServiceRegister,
        DNSServiceProcessResult,
        kDNSServiceErr_NoError
    )
    bonjour = True
except ImportError:
    bonjour = False

class Daapd:
    """
    This is the main class for the DAAP daemon. An instance is a WSGI app, so you
    should be able to plug it into any WSGI compatible server and start
    serving up music, just like that.

    This also provides mDNS integration, so without any effort on the user's
    part, the server will broadcast its presence to the world (some
    configuration required).

    This class does not actually serve any music metadata. To do that, you should
    derive from this class and translate whatever metadata API you have into
    the API provided by this class.

    Refer to http://tapjam.net/daap/ for the DAAP specification.
    """

    def __init__(self, port=3689, autodiscover=True, name="DAAP-Train"):
        """
        If autodiscover is True, informs the local network that there is a
        daap server located on <port>.
        """
        if autodiscover and bonjour:
            self.sdRef = DNSServiceRegister(
                name = name, 
                regtype = '_daap._tcp.', 
                port = port,
                callBack = self._registered_callback)

    def server_info(self, request):
        pass

    def content_codes(self, request):
        pass

    def login(self, request):
        pass

    def update(self, request):
        pass

    def databases(self, request):
        pass

    def __call__(self, environ, start_response):
        req = Request(environ)
        function = req.path_info.strip('/')
        if hasattr(self, function) and \
                not function.startswith('_') and \
                callable(getattr(self, function)):
            try:
                resp = getattr(self, function)(req)
            except exc.HttpException, e:
                resp = e

            if not isinstance(resp, Response):
                resp = Response(body=resp)
            return resp(environ, start_response)

        return exc.HTTPNotFound()(environ, start_response)

    # Helper and private functions. I wouldn't override these unless you
    # know what you're doing.

    def _registered_callback(sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == kDNSServiceErr_NoError:
            self.sdRef = sdRef
            self._pb_thread = Thread(
                None, 
                self._pb_discovery, 
                "Bonjour Discovery Thread")
            self._pb_thread.daemon = True
            self._pb_thread.start()

    def _pb_discovery():
        try:
            while True:
                ready = select.select([self.sdRef], [], [])
                if self.sdRef in ready[0]:
                    DNSServiceProcessResult(self.sdRef)
        finally:
            self.sdRef.close()
