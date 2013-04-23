'''
Created on Aug 9, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the method override header handling.
'''

from ally.container.ioc import injected
from ally.core.http.spec.server import METHODS_TO_CORE, UNKNOWN
from ally.design.context import Context, requires, defines
from ally.design.processor import HandlerProcessorProceed
from ally.http.spec.codes import INVALID_HEADER_VALUE
from ally.http.spec.server import IDecoderHeader, METHOD_GET, METHOD_POST, \
    METHOD_DELETE, METHOD_PUT
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    decoderHeader = requires(IDecoderHeader)
    methodName = requires(str)
    # ---------------------------------------------------------------- Defined
    method = defines(int)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(int)
    isSuccess = defines(bool)
    text = defines(str)
    errorMessage = defines(str)

# --------------------------------------------------------------------

@injected
class MethodHandler(HandlerProcessorProceed):
    '''
    Provides the method override processor.
    '''

    nameXMethodOverride = 'X-HTTP-Method-Override'
    # The header name for the method override.
    methodsOverride = {
                       METHOD_GET: {METHOD_GET, METHOD_DELETE},
                       METHOD_POST: {METHOD_POST, METHOD_PUT}
                       }
    # A dictionary containing as a key the original method and as a value the methods that are allowed for override.

    def __init__(self):
        assert isinstance(self.nameXMethodOverride, str), 'Invalid method override name %s' % self.nameXMethodOverride
        assert isinstance(self.methodsOverride, dict), 'Invalid methods override %s' % self.methodsOverride
        super().__init__()

    def process(self, request:Request, response:Response, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Overrides the request method based on a provided header.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        if response.isSuccess is False: return  # Skip in case the response is in error

        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid header decoder %s' % request.decoderHeader

        value = request.decoderHeader.retrieve(self.nameXMethodOverride)
        if value:
            
            allowed = self.methodsOverride.get(request.methodName)
            if not allowed:
                response.code, response.isSuccess = INVALID_HEADER_VALUE
                response.text = 'Cannot override method'
                return

            if value not in allowed:
                response.code, response.isSuccess = INVALID_HEADER_VALUE
                response.text = 'Override method \'%s\' not allowed' % value
                return

            assert log.debug('Successfully overridden method %s with %s', request.methodName, value) or True
            request.methodName = value
            
        request.method = METHODS_TO_CORE.get(request.methodName, UNKNOWN)
