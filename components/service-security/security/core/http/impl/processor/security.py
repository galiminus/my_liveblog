'''
Created on Apr 12, 2012

@package: security service
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the security check for incoming requests by using the Access service.
'''

from ally.container.ioc import injected
from ally.design.bean import Bean, Attribute
from ally.design.context import Context, requires, defines
from ally.design.processor import Processing, Chain, Handler, Assembly, Function, \
    NO_VALIDATION
from ally.http.spec.codes import PATH_NOT_FOUND
from ally.http.spec.server import RequestHTTP, ResponseHTTP, ResponseContentHTTP, \
    IDecoderHeader, METHOD_GET, METHOD_OPTIONS
from ally.support.util_io import IInputStream, writeGenerator
from datetime import datetime, timedelta
from io import BytesIO
from sched import scheduler
from threading import Thread
import codecs
import json
import logging
import re
import time

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    methodName = requires(str)
    uriRoot = requires(str)
    uri = requires(str)
    parameters = requires(list)
    headers = requires(dict)
    decoderHeader = requires(IDecoderHeader)

class RequestContent(Context):
    '''
    The request content context.
    '''
    # ---------------------------------------------------------------- Required
    source = requires(IInputStream)

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(int)
    isSuccess = defines(bool)
    text = defines(str)
    headers = defines(dict)

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    source = defines(IInputStream)
    length = defines(int)
    type = defines(str)
    charSet = defines(str)

# --------------------------------------------------------------------

@injected
class SecurityHandler(Handler):
    '''
    Implementation for a handler that provides the security check by using REST data received from either internal or
    external server. The Access structure is defined as in the @see: security-http-acl plugin.
    '''

    requestAssembly = Assembly
    # The assembly of processors used for handling the requests.

    nameAuthorization = 'Authorization'
    # The header name for the session identifier.

    accessHeaders = dict
    # The headers used in getting the access data.
    accessUriRoot = str
    # The root URI of the access URI.
    accessUri = str
    # The access URI to fetch the Access objects from, this URI needs to have a marker '*' where the actual authentication
    # code will be placed, also this URI needs to return json encoded Access objects.
    accessParameters = list
    # The list of parameters to use for the access call.
    accessResponseEncoding = str
    # The access response encoding.
    cleanupTimeout = float
    # The number of seconds of inactivity after which a cached access is cleared.

    def __init__(self):
        assert isinstance(self.requestAssembly, Assembly), 'Invalid request assembly %s' % self.requestAssembly
        assert isinstance(self.nameAuthorization, str), 'Invalid authorization name %s' % self.nameAuthorization
        assert isinstance(self.accessHeaders, dict), 'Invalid access headers %s' % self.accessHeaders
        assert isinstance(self.accessUriRoot, str), 'Invalid access URI root %s' % self.accessUriRoot
        assert isinstance(self.accessUri, str), 'Invalid access URI %s' % self.accessUri
        assert isinstance(self.accessParameters, list), 'Invalid access parameters %s' % self.accessParameters
        assert isinstance(self.accessResponseEncoding, str), \
        'Invalid access response encoding %s' % self.accessResponseEncoding
        assert isinstance(self.cleanupTimeout, int), 'Invalid cleanup time out %s' % self.cleanupTimeout

        requestProcessing = self.requestAssembly.create(NO_VALIDATION, request=Request, requestCnt=RequestContent,
                                                        response=Response, responseCnt=ResponseContent)
        assert isinstance(requestProcessing, Processing), 'Invalid processing %s' % requestProcessing
        super().__init__(Function(requestProcessing.contexts, self.process))

        self._requestProcessing = requestProcessing
        self._cache = Cache()

        self._authenticationTimeOut = timedelta(seconds=self.cleanupTimeout)
        schedule = scheduler(time.time, time.sleep)
        def executeCleanup():
            self._cleanInactiveAccesses()
            schedule.enter(self.cleanupTimeout, 1, executeCleanup, ())
        schedule.enter(self.cleanupTimeout, 1, executeCleanup, ())
        scheduleRunner = Thread(name='Cleanup access/sessions thread', target=schedule.run)
        scheduleRunner.daemon = True
        scheduleRunner.start()

        self._contentType = 'text/json'
        self._charSet = 'utf-8'
        self._unauthorizedAccess = b'{"code":"401","message":"Unauthorized access"}'
        self._invalidAccess = b'{"code":"401","message":"Invalid authorization"}'
        self._forbiddenAccess = b'{"code":"403","message":"Forbidden access"}'
        self._notFound = b'{"code":"404","message":"Not Found"}'

    def process(self, chain, request, requestCnt, response, responseCnt):
        '''
        Process the redirect.

        @param requestProcessing: Processing
            The processing that provides the request handling chain.

        The rest of the parameters are contexts.
        '''
        assert isinstance(chain, Chain), 'Invalid processors chain %s' % chain
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(requestCnt, RequestContent), 'Invalid request content %s' % requestCnt
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        if response.isSuccess is False: return  # Skip in case the response is in error

        assert isinstance(request.decoderHeader, IDecoderHeader), 'Invalid decoder header %s' % request.decoderHeader

        if request.methodName == METHOD_OPTIONS:
            chain.branch(self._requestProcessing)
            return

        authentication = request.decoderHeader.retrieve(self.nameAuthorization)
        if not authentication:
            response.code, response.isSuccess = 401, False
            response.text = 'Unauthorized access'
            responseCnt.source = BytesIO(self._unauthorizedAccess)
            responseCnt.length = len(self._unauthorizedAccess)
            responseCnt.type, responseCnt.charSet = self._contentType, self._charSet
            chain.proceed()
            return

        cacheAuth = self._cache.authentications.get(authentication)
        if not cacheAuth:
            accesses = self._access(authentication, request)
            if accesses is None:
                response.code, response.isSuccess = 401, False
                response.text = 'Invalid authorization'
                responseCnt.source = BytesIO(self._invalidAccess)
                responseCnt.length = len(self._invalidAccess)
                responseCnt.type, responseCnt.charSet = self._contentType, self._charSet
                chain.proceed()
                return
            cacheAuth = self._cache.authentications[authentication] = self._cacheAccess(accesses, authentication)

        forward, found = False, False

        assert isinstance(cacheAuth, CacheAuthentication)
        cacheAuth.lastAccess = datetime.now()
        cacheMethod = cacheAuth.methods.get(request.methodName)
        if cacheMethod:
            assert isinstance(cacheMethod, CacheMethod)
            for cachePattern in cacheMethod.patterns:
                assert isinstance(cachePattern, CachePattern)
                match = cachePattern.pattern.match(request.uri)
                if match:
                    found = True
                    for k, resource in enumerate(match.groups()):
                        try: cacheFilter = cachePattern.filters[k]
                        except IndexError:
                            raise Exception('Invalid filter at position %s in pattern %s' %
                                            (k, cachePattern.pattern.pattern))
                        assert isinstance(cacheFilter, CacheFilter)
                        value = cacheFilter.accesses.get(resource)
                        if value is None:
                            uri = cacheFilter.uri.replace('*', resource)
                            value = cacheFilter.accesses[resource] = self._isAllowed(request, uri)
                            if not value: break
                        elif not value: break
                    else: forward = True
                    break

        if not forward:
            if found:
                response.code, response.isSuccess = 403, False
                response.text = 'Forbidden access'
                responseCnt.source = BytesIO(self._forbiddenAccess)
                responseCnt.length = len(self._forbiddenAccess)
            else:
                response.code, response.isSuccess = PATH_NOT_FOUND
                response.text = 'Not Found'
                responseCnt.source = BytesIO(self._notFound)
                responseCnt.length = len(self._notFound)
            responseCnt.type, responseCnt.charSet = self._contentType, self._charSet
            chain.proceed()
            return

        chain.branch(self._requestProcessing)

    # ----------------------------------------------------------------

    def _cacheAccess(self, accesses, authentication):
        '''
        Creates the cache for the provided access response.
        '''
        assert isinstance(accesses, dict), 'Invalid accesses %s' % accesses
        assert isinstance(authentication, str), 'Invalid authentication %s' % authentication

        accesses = accesses['AccessList']  # Get the access object list
        cacheAuth = CacheAuthentication()
        for access in accesses:  # Get the access object
            assert isinstance(access, dict), 'Invalid access object %s' % access
            pattern = re.compile(access['Pattern'])  # Get the pattern
            filters = access.get('Filter')  # Get the filters is available
            if filters is not None: filters = [CacheFilter(uri=uri) for uri in filters['Filter']]

            for method in access['Methods']['Methods']:  # Get the methods
                cacheMethod = cacheAuth.methods.get(method)
                if not cacheMethod: cacheMethod = cacheAuth.methods[method] = CacheMethod()
                cacheMethod.patterns.append(CachePattern(pattern=pattern, filters=filters))

        return cacheAuth

    def _access(self, authentication, request):
        '''
        Retrieve the access for the authentication.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request
        assert isinstance(authentication, str), 'Invalid authentication %s' % authentication

        req, reqCnt = self._requestProcessing.contexts['request'](), self._requestProcessing.contexts['requestCnt']()
        rsp, rspCnt = self._requestProcessing.contexts['response'](), self._requestProcessing.contexts['responseCnt']()
        assert isinstance(req, RequestHTTP)
        assert isinstance(rsp, ResponseHTTP)
        assert isinstance(rspCnt, ResponseContentHTTP)

        req.methodName = METHOD_GET
        req.scheme = request.scheme
        req.headers = self.accessHeaders
        req.uriRoot = self.accessUriRoot
        req.uri = self.accessUri.replace('*', authentication)
        req.parameters = self.accessParameters

        requestChain = Chain(self._requestProcessing)
        requestChain.process(request=req, requestCnt=reqCnt, response=rsp, responseCnt=rspCnt).doAll()
        if not rsp.isSuccess: return
        if rspCnt.source is None:
            raise Exception('Problems with security access, the URI \'%s\' has a response %s %s, but no content' %
                            (self.accessUriRoot + self.accessUri, rsp.code, rsp.text))
        if isinstance(rspCnt.source, IInputStream):
            source = rspCnt.source
        else:
            source = BytesIO()
            for bytes in rspCnt.source: source.write(bytes)
            source.seek(0)
        return json.load(codecs.getreader(self.accessResponseEncoding)(source))

    def _isAllowed(self, request, uri):
        '''
        Retrieve the access for the authentication.
        '''
        assert isinstance(request, Request), 'Invalid request %s' % request

        req, reqCnt = self._requestProcessing.contexts['request'](), self._requestProcessing.contexts['requestCnt']()
        rsp, rspCnt = self._requestProcessing.contexts['response'](), self._requestProcessing.contexts['responseCnt']()
        assert isinstance(req, RequestHTTP)
        assert isinstance(rsp, ResponseHTTP)
        assert isinstance(rspCnt, ResponseContentHTTP)

        req.methodName = METHOD_GET
        req.scheme = request.scheme
        req.headers = self.accessHeaders
        req.uriRoot = self.accessUriRoot
        req.uri = uri

        requestChain = Chain(self._requestProcessing)
        requestChain.process(request=req, requestCnt=reqCnt, response=rsp, responseCnt=rspCnt).doAll()
        if not rsp.isSuccess: return
        if rspCnt.source is None:
            raise Exception('Problems with security filter access, the URI \'%s\' has a response %s %s, but no content' %
                            (self.accessUriRoot + uri, rsp.code, rsp.text))
        if isinstance(rspCnt.source, IInputStream):
            source = rspCnt.source
        else:
            source = BytesIO()
            for bytes in rspCnt.source: source.write(bytes)
            source.seek(0)
        allowed = json.load(codecs.getreader(self.accessResponseEncoding)(source))
        return allowed['HasAccess'] == 'True'

    def _cleanInactiveAccesses(self):
        '''
        Called in order to clean the inactive access sessions.
        '''
        current, expired = datetime.now() - self._authenticationTimeOut, []
        for authentication, cacheAuth in self._cache.authentications.items():
            assert isinstance(cacheAuth, CacheAuthentication)
            if current > cacheAuth.lastAccess: expired.append(authentication)

        assert log.debug('Clearing %s sessions at %s' % (len(expired), datetime.now())) or True
        for authentication in expired: self._cache.authentications.pop(authentication, None)

# --------------------------------------------------------------------

class Cache(Bean):
    '''
    The cache object.
    '''

    authentications = dict; authentications = Attribute(authentications, factory=dict, doc='''
    @rtype: dictionary{string, CacheAuthentication}
    The cached authentication indexed by authentication code.
    ''')

class CacheAuthentication(Bean):
    '''
    The authentication cache object.
    '''

    methods = dict; methods = Attribute(methods, factory=dict, doc='''
    @rtype: dictionary{string, CacheMethod}
    The cached method indexed by method name.
    ''')
    lastAccess = datetime; lastAccess = Attribute(lastAccess, doc='''
    @rtype: datetime
    The last time this cached authentication was used.
    ''')

class CacheMethod(Bean):
    '''
    The method cache object.
    '''

    patterns = list; patterns = Attribute(patterns, factory=list, doc='''
    @rtype: list[CachePattern]
    The cached patterns.
    ''')

class CachePattern(Bean):
    '''
    The pattern cache object.
    '''

    pattern = object; pattern = Attribute(pattern, doc='''
    @rtype: object
    The compiled regex pattern.
    ''')
    filters = list; filters = Attribute(filters, factory=list, doc='''
    @rtype: list[CacheFilter]
    The cached filters.
    ''')

class CacheFilter(Bean):
    '''
    The filter cache object.
    '''

    uri = str; uri = Attribute(uri, doc='''
    @rtype: string
    The uri pattern to call the filter.
    ''')
    accesses = dict; accesses = Attribute(accesses, factory=dict, doc='''
    @rtype: dictionary{string: boolean}
    The cached accesses for the filter.
    ''')
