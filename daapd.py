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
from daap_types import *
import struct
import select

__all__ = ['Daapd', 'DaapServerInfo']

try:
    from pybonjour import (
        DNSServiceRegister,
        DNSServiceProcessResult,
        kDNSServiceErr_NoError,
        TXTRecord
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

    name = "The Music Train"

    def __init__(self, port=3689, autodiscover=True, name=name):
        """
        If autodiscover is True, informs the local network that there is a
        daap server located on <port>.
        """
        self.name = name
        self.autodiscover = autodiscover
        self.port = port

    def discover(self):
        if self.autodiscover and bonjour:
            txt_record = TXTRecord()
            txt_record['txtvers'] = '1'
            txt_record['iTSh Version'] = '131073'
            txt_record['Machine Name'] = self.name
            txt_record['Password'] = 'false'

            self.sdRef = DNSServiceRegister(
                name = self.name,
                regtype = '_daap._tcp',
                port = self.port,
                callBack = self._registered_callback,
                txtRecord = txt_record)

            self._pb_thread = Thread(
                None,
                self._pb_discovery,
                "Bonjour Discovery Thread")
            self._pb_thread.daemon = True
            self._pb_thread.start()

    def server_info(self, request):
        """
        Request: daap://server/server-info (or http://server:3689/)
        Response: msrv
        Description: Provides basic negotiation info on what the server does
            and doesn't support and protocols.
        Content: (See appendix A for detailed information on codes)
            msrv
              mstt - status
              apro - daap protocol
              msix - does the server support indexing?
              msex - does the server support extensions?
              msup - does the server support update?
              msal - does the server support auto-logout?
              mstm - timeout interval
              mslr - is login required?
              msqy - does the server support queries?
              minm - server name
              msrs - does the server support resolve?  (needs persistent ids)
              msbr - does the server support browsing?
              mspi - does the server support persistent ids?
              mpro - dmap protocol version
        """
        print "Getting server info"
        return DaapServerInfo(name=self.name, login=False)

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
        function = req.path_info.strip('/').replace('-', '_')
        if hasattr(self, function) and \
                not function.startswith('_') and \
                callable(getattr(self, function)):
            try:
                resp = getattr(self, function)(req)
            except exc.HTTPException, e:
                resp = e

            if not isinstance(resp, Response):
                resp = Response(body=resp)
            return resp(environ, start_response)

        return exc.HTTPNotFound()(environ, start_response)

    # Helper and private functions. I wouldn't override these unless you
    # know what you're doing.

    def _registered_callback(self, sdRef, flags, errorCode, name, regtype, domain):
        print "Maybe should do something?"
        pass

    def _pb_discovery(self):
        try:
            while True:
                print "blocking"
                DNSServiceProcessResult(self.sdRef)
                print "oh boy!"
        finally:
            self.sdRef.close()


def code_to_integer(code):
    number = 0
    for i in xrange(len(code)):
        char = code[i]
        number |= ord(char) << i*8
    return number

codes = {
    # Top level
    'server-info': code_to_integer('msrv'),
    'content-codes': code_to_integer('mccr'),
    'login': code_to_integer('mlog'),
    'update': code_to_integer('mupd'),
    'databases': code_to_integer('avdb'),
    'items': code_to_integer('adbs'),
    'containers': code_to_integer('aply'),
    'playlist': code_to_integer('apso'),

    # info
    'status': code_to_integer('mstt'),
    'protocol': code_to_integer('apro'),
    'indexing': code_to_integer('msix'),
    'extensions': code_to_integer('msex'),
    'update': code_to_integer('msup'),
    'auto_logout': code_to_integer('msal'),
    'timeout': code_to_integer('mstm'),
    'login': code_to_integer('mslr'),
    'queries': code_to_integer('msqy'),
    'name': code_to_integer('minm'),
    'resolve': code_to_integer('msrs'),
    'browsing': code_to_integer('msbr'),
    'persistent_ids': code_to_integer('mspi'),
    'dmap_protocol': code_to_integer('mpro')
}

class DaapServerInfo:
    """
    Represents a ServerInfo packet
    """

    """
        msrv - list
          mstt - status - integer
          apro - daap protocol - version (2 shorts)
          msix - does the server support indexing - bool
          msex - does the server support extensions - bool
          msup - does the server support update - bool
          msal - does the server support auto-logout - bool
          mstm - timeout interval - integer
          mslr - is login required - bool
          msqy - does the server support queries - bool
          minm - server name - string
          msrs - does the server support resolve - bool
          msbr - does the server support browsing - bool
          mspi - does the server support persistent ids = bool
          mpro - dmap protocol version - version (2 shorts)
    """

    def __init__(self,
            status = 200,
            version = (2,0),
            indexing = False,
            extensions = False,
            update = False,
            auto_logout = False,
            timeout = 5000,
            login = False,
            queries = True,
            name = "daap-train",
            resolve = False,
            browsing = True,
            persistent_ids = False,
            dmap_protocol = (1, 0)):

        self.data = DaapList(codes['server-info'])
        self.data.append(DaapInt(codes['status'], status))
        self.data.append(DaapVersion(codes['protocol'], version))
        self.data.append(DaapString(codes['name'], name))
        self.data.append(DaapVersion(codes['dmap_protocol'], dmap_protocol))
        self.data.append(DaapInt(codes['timeout'], timeout))

        # Options
        self.data.append(DaapBool(codes['indexing'], indexing))
        self.data.append(DaapBool(codes['extensions'], extensions))
        self.data.append(DaapBool(codes['update'], update))
        self.data.append(DaapBool(codes['auto_logout'], auto_logout))
        self.data.append(DaapBool(codes['login'], login))
        self.data.append(DaapBool(codes['queries'], queries))
        self.data.append(DaapBool(codes['resolve'], resolve))
        self.data.append(DaapBool(codes['browsing'], browsing))
        self.data.append(DaapBool(codes['persistent_ids'], persistent_ids))

    def __str__(self):
        return str(self.data)

    def __len__(self):
        return 4
