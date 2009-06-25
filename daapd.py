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

"""
This is the interface that represents the server side of the daap protocol.
"""

from webob import Request, Response, exc

class Daapd:
    """
    Abstract interface representing DAAP interactions. Something that can
    actually provide legitimate data should derive from this and implement
    the functions appropriately.
    """
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
        if hasattr(self, function):
            try:
                resp = getattr(self, function)(req) or ''
            except exc.HttpException, e:
                resp = e

            if isinstance(resp, basestring):
                resp = Response(body=resp)
            return resp(environ, start_response)

        return exc.HTTPNotFound()(environ, start_response)
