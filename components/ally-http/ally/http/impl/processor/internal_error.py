'''
Created on Jun 22, 2012

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the internal error representation. This is usually when the server fails badly.
'''

from ally.container.ioc import injected
from ally.design.context import defines, Context, optional
from ally.design.processor import HandlerProcessor, Chain
from ally.http.spec.codes import INTERNAL_ERROR
from ally.support.util_io import convertToBytes, IInputStream
from collections import Iterable
from functools import partial
from io import StringIO, BytesIO
import logging
import traceback

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(int)
    isSuccess = defines(bool)
    text = defines(str)
    errorMessage = defines(str)
    headers = defines(dict)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Optional
    source = optional(IInputStream, Iterable)

# --------------------------------------------------------------------

@injected
class InternalErrorHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the handling of internal errors.
    '''

    errorHeaders = {'Content-Type':'text'}
    # The headers that will be placed on the response.

    def __init__(self):
        '''
        Construct the internal error handler.
        '''
        assert isinstance(self.errorHeaders, dict), 'Invalid error headers %s' % self.errorHeaders
        super().__init__()

    def process(self, chain, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the additional arguments by type to be populated.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt

        chain.callBackError(partial(self.handleError, chain, response, responseCnt))
        if __debug__:
            # If in debug mode and the response content has a source generator then we will try to read that
            # in order to catch any exception before the actual streaming.
            def onFinalize():
                '''
                Handle the finalization
                '''
                if isinstance(responseCnt.source, Iterable):
                    content = BytesIO()
                    try:
                        for bytes in responseCnt.source: content.write(bytes)
                    except:
                        log.exception('Exception occurred while processing the chain')
                        error = StringIO()
                        traceback.print_exc(file=error)
                        response.code, response.isSuccess = INTERNAL_ERROR
                        response.text = 'Cannot render response, please consult the server logs'
                        response.headers = self.errorHeaders
                        responseCnt.source = convertToBytes(self.errorResponse(error), 'utf8', 'backslashreplace')
                    else:
                        content.seek(0)
                        responseCnt.source = content
            
            chain.callBack(onFinalize)
            
    def handleError(self, chain, response, responseCnt):
        '''
        Handle the error.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        # If there is an explanation for the error occurred, we do not need to make another one
        if ResponseContent.source in responseCnt: return
        
        log.exception('Exception occurred while processing the chain')
        error = StringIO()
        traceback.print_exc(file=error)
        response.code, response.isSuccess = INTERNAL_ERROR
        response.text = 'Upps, please consult the server logs'
        response.headers = self.errorHeaders
        responseCnt.source = convertToBytes(self.errorResponse(error), 'utf8', 'backslashreplace')

    def errorResponse(self, error):
        '''
        Generates the error response.
        
        @param error: StringIO
            The error stream that contains the stack info.
        '''
        assert isinstance(error, IInputStream), 'Invalid error stream %s' % error

        yield 'Internal server error occurred, this is a major issue so please contact your administrator\n\n'
        error.seek(0)
        yield error.read()
        
