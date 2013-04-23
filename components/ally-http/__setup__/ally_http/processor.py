'''
Created on Nov 24, 2011

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from ally.container import ioc
from ally.design.processor import Handler
from ally.http.impl.processor.header import HeaderHandler
from ally.http.impl.processor.headers.content_length import \
    ContentLengthDecodeHandler, ContentLengthEncodeHandler
from ally.http.impl.processor.headers.content_type import \
    ContentTypeDecodeHandler, ContentTypeEncodeHandler
from ally.http.impl.processor.internal_error import InternalErrorHandler

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def read_from_params():
    '''If true will also read header values that are provided as query parameters'''
    return True

# --------------------------------------------------------------------

@ioc.entity
def internalError(): return InternalErrorHandler()

@ioc.entity
def header() -> Handler:
    b = HeaderHandler()
    b.useParameters = read_from_params()
    return b

# --------------------------------------------------------------------
# Header decoders

@ioc.entity
def contentTypeDecode() -> Handler: return ContentTypeDecodeHandler()

@ioc.entity
def contentLengthDecode() -> Handler: return ContentLengthDecodeHandler()


# --------------------------------------------------------------------
# Header encoders

@ioc.entity
def contentTypeEncode() -> Handler: return ContentTypeEncodeHandler()

@ioc.entity
def contentLengthEncode() -> Handler: return ContentLengthEncodeHandler()
