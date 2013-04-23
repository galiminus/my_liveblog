'''
Created on Apr 12, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the content location redirect based on references.
'''

from ally.api.operator.type import TypeModelProperty
from ally.api.type import TypeReference
from ally.container.ioc import injected
from ally.core.http.spec.server import IEncoderPath
from ally.core.spec.codes import REDIRECT
from ally.core.spec.resources import Invoker
from ally.design.context import Context, requires, defines
from ally.design.processor import Handler, Assembly, NO_VALIDATION, Processing, \
    Chain, Function
from ally.http.spec.server import IEncoderHeader
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    invoker = requires(Invoker)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    encoderHeader = requires(IEncoderHeader)
    encoderPath = requires(IEncoderPath)
    obj = requires(object)
    # ---------------------------------------------------------------- Defined
    code = defines(int)
    isSuccess = defines(bool)
    text = defines(str)

# --------------------------------------------------------------------

@injected
class RedirectHandler(Handler):
    '''
    Implementation for a processor that provides the redirect by using the content location based on found references.
    '''

    nameLocation = 'Location'
    # The header name for the location redirect.
    redirectAssembly = Assembly
    # The redirect processors, among this processors it has to be one to fetch the location object.

    def __init__(self):
        assert isinstance(self.redirectAssembly, Assembly), 'Invalid redirect assembly %s' % self.redirectAssembly
        assert isinstance(self.nameLocation, str), 'Invalid string %s' % self.nameLocation

        redirectProcessing = self.redirectAssembly.create(NO_VALIDATION, request=Request, response=Response)
        assert isinstance(redirectProcessing, Processing), 'Invalid processing %s' % redirectProcessing
        super().__init__(Function(redirectProcessing.contexts, self.process))
        
        self._redirectProcessing = redirectProcessing

    def process(self, chain, request, response, **keyargs):
        '''
        Process the redirect.
        
        The rest of the parameters are contexts.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        if response.isSuccess is not False:  # Skip in case the response is in error
            assert isinstance(request.invoker, Invoker), 'Invalid request invoker %s' % request.invoker

            typ = request.invoker.output
            if isinstance(typ, TypeModelProperty): typ = typ.type
            if isinstance(typ, TypeReference):
                redirectChain = Chain(self._redirectProcessing)
                redirectChain.process(request=request, response=response, **keyargs).doAll()
                if response.isSuccess is not False:
                    assert isinstance(response.encoderHeader, IEncoderHeader), \
                    'Invalid header encoder %s' % response.encoderHeader
                    assert isinstance(response.encoderPath, IEncoderPath), \
                    'Invalid encoder path %s' % response.encoderPath

                    response.encoderHeader.encode(self.nameLocation, response.encoderPath.encode(response.obj))
                    response.code, response.isSuccess = REDIRECT
                    response.text = 'Redirect'
                    return

        chain.proceed()
