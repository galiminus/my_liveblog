'''
Created on Jun 22, 2012

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provide the internal error representation. This is usually when the server fails badly.
'''

from ally.container.ioc import injected
from ally.design.processor import Chain
from ally.exception import DevelError
from ally.http.impl.processor.internal_error import InternalErrorHandler, \
    ResponseContent, Response
from ally.http.spec.codes import INVALID_REQUEST
import logging
import sys

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
class InternalDevelErrorHandler(InternalErrorHandler):
    '''
    Extension for @see: InternalErrorHandler that better handles the DevelError.
    '''
            
    def handleError(self, chain, response, responseCnt):
        '''
        Handle the error.
        @see: InternalErrorHandler.handleError
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        
        # If there is an explanation for the error occurred, we do not need to make another one
        if ResponseContent.source in responseCnt: return

        exc = sys.exc_info()[1]
        if isinstance(exc, DevelError):
            log.warn('Development error occurred while processing the chain', exc_info=True)
            response.code, response.isSuccess = INVALID_REQUEST
            response.text, response.errorMessage = 'Development error', str(exc)
            chain.proceed()
            # We try to process now the chain (where it left of) with the exception set.
            return
        
        super().handleError(chain, response, responseCnt)
