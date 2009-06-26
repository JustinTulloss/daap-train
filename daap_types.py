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

import struct

class DaapType(object):
    def __init__(self, code, value):
        self.code = code
        self.value = value
        self.data = struct.pack(self.format, code, self.size, value)

    def __str__(self):
        return str(self.data)

    def __len__(self):
        return len(self.data)

class DaapBool(DaapType):
    format = "iiB"
    size = 1

class DaapByte(DaapType):
    format = "iib"
    size = 1

class DaapUByte(DaapType):
    format = "iiB"
    size = 1

class DaapShort(DaapType):
    format = "iih"
    size = 2

class DaapUShort(DaapType):
    format = "iiH"
    size = 2

class DaapInt(DaapType):
    format = "iii"
    size = 4

class DaapUInt(DaapType):
    format = "iiI"
    size = 4

class DaapLong(DaapType):
    format = "iiq"
    size = 8

class DaapULong(DaapType):
    format = "iiQ"
    size = 8

class DaapString(DaapType):
    format = "ii%ds"
    def __init__(self, code, value):
        self.size = len(value)
        self.format = self.format % self.size
        super(DaapString, self).__init__(code, value)

class DaapDate(DaapType):
    format = "iii"
    size = 4

class DaapVersion(DaapType, list):
    format = "iihh"
    size = 4
    def __init__(self, code, value):
        """
        Value should be a tuple: (major, minor)
        """
        self.code = code
        self.value = value
        self.data = struct.pack(self.format, code, self.size, *value)

class DaapList(DaapType, list):
    format = "ii%dp"
    def __init__(self, code):
        super(list, self).__init__()
        self.code = code

    def __len__(self):
        return 0

    def __str__(self):
        buffer = ''
        for item in self:
            # TODO: Make sure it subclasses DaapType
            buffer += str(item)
        size = len(buffer)
        format = self.format % size
        return struct.pack(format, self.code, size, buffer)

    def __repr__(self):
        return str(self)
