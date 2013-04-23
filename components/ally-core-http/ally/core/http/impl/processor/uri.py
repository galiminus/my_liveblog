'''
Created on Jun 28, 2011

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the URI request path handler.
'''

from ally.api.type import Scheme
from ally.container.ioc import injected
from ally.core.http.spec.codes import MISSING_HEADER
from ally.core.http.spec.server import IEncoderPath
from ally.core.spec.codes import RESOURCE_NOT_FOUND, RESOURCE_FOUND
from ally.core.spec.resources import ConverterPath, Path, Converter, Normalizer, \
    Node
from ally.design.context import Context, requires, defines, optional
from ally.design.processor import HandlerProcessorProceed
from ally.http.spec.server import IDecoderHeader
from ally.support.core.util_resources import findPath
from collections import deque
from urllib.parse import urlencode, urlunsplit, urlsplit, quote, unquote
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Request(Context):
    '''
    The request context.
    '''
    # ---------------------------------------------------------------- Required
    scheme = requires(str)
    uriRoot = requires(str)
    uri = requires(str)
    decoderHeader = requires(IDecoderHeader)
    # ---------------------------------------------------------------- Optional
    argumentsOfType = optional(dict)
    # ---------------------------------------------------------------- Defined
    path = defines(Path, doc='''
    @rtype: Path
    The path to the resource node.
    ''')
    converterId = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for model id's.
    ''')
    normalizerParameters = defines(Normalizer, doc='''
    @rtype: Normalizer
    The normalizer to use for decoding parameters names.
    ''')
    converterParameters = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for the parameters values.
    ''')

class Response(Context):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    code = defines(int)
    isSuccess = defines(bool)
    text = defines(str)
    converterId = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for model id's.
    ''')
    encoderPath = defines(IEncoderPath, doc='''
    @rtype: IEncoderPath
    The path encoder used for encoding paths that will be rendered in the response.
    ''')

class ResponseContent(Context):
    '''
    The response content context.
    '''
    # ---------------------------------------------------------------- Defined
    type = defines(str, doc='''
    @rtype: string
    The response content type.
    ''')

# --------------------------------------------------------------------

@injected
class URIHandler(HandlerProcessorProceed):
    '''
    Implementation for a processor that provides the searches based on the request URL the resource path, also
    populates the parameters and extension format on the request.
    '''

    resourcesRoot = Node
    # The resources node that will be used for finding the resource path.
    converterPath = ConverterPath
    # The converter path used for handling the URL path.
    headerHost = 'Host'
    # The header in which the host is provided.

    def __init__(self):
        assert isinstance(self.resourcesRoot, Node), 'Invalid resources node %s' % self.resourcesRoot
        assert isinstance(self.converterPath, ConverterPath), 'Invalid ConverterPath object %s' % self.converterPath
        assert isinstance(self.headerHost, str), 'Invalid string %s' % self.headerHost
        super().__init__()

    def process(self, request:Request, response:Response, responseCnt:ResponseContent, **keyargs):
        '''
        @see: HandlerProcessorProceed.process
        
        Process the URI to a resource path.
        '''
        assert isinstance(request, Request), 'Invalid required request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response
        assert isinstance(responseCnt, ResponseContent), 'Invalid response content %s' % responseCnt
        assert isinstance(request.uri, str), 'Invalid request URI %s' % request.uri
        if response.isSuccess is False: return  # Skip in case the response is in error

        paths = request.uri.split('/')
        i = paths[-1].rfind('.') if len(paths) > 0 else -1
        if i < 0:
            extension = None
        else:
            extension = paths[-1][i + 1:].lower()
            paths[-1] = paths[-1][0:i]
        paths = [unquote(p) for p in paths if p]

        request.path = findPath(self.resourcesRoot, paths, self.converterPath)
        assert isinstance(request.path, Path), 'Invalid path %s' % request.path
        if not request.path.node:
            # we stop the chain processing
            response.code, response.isSuccess = RESOURCE_NOT_FOUND
            response.text = 'Cannot find resources for path'
            assert log.debug('No resource found for URI %s', request.uri) or True
            return
        assert log.debug('Found resource for URI %s', request.uri) or True

        request.converterId = self.converterPath
        request.converterParameters = self.converterPath
        request.normalizerParameters = self.converterPath

        if Request.argumentsOfType in request: request.argumentsOfType[Scheme] = request.scheme

        assert isinstance(request.decoderHeader, IDecoderHeader), \
        'Invalid request decoder header %s' % request.decoderHeader
        assert isinstance(request.uriRoot, str), 'Invalid request root URI %s' % request.uriRoot
        host = request.decoderHeader.retrieve(self.headerHost)
        if host is None:
            response.code, response.isSuccess = MISSING_HEADER
            response.text = 'Missing the %s header' % self.headerHost
            assert log.debug('No host header available for URI %s', request.uri) or True
            return
        response.encoderPath = EncoderPathURI(request.scheme, host, request.uriRoot, self.converterPath, extension)

        response.code, response.isSuccess = RESOURCE_FOUND
        response.converterId = self.converterPath
        if extension: responseCnt.type = extension

# --------------------------------------------------------------------

class EncoderPathURI(IEncoderPath):
    '''
    Provides encoding for the URI paths generated by the URI processor.
    '''

    __slots__ = ('scheme', 'host', 'root', 'converterPath', 'extension')

    def __init__(self, scheme, host, root, converterPath, extension):
        '''
        @param scheme: string
            The encoded path scheme.
        @param host: string
            The host string.
        @param root: string
            The root URI to be considered for constructing a request path, basically the relative path root. None if the path
            is not relative.
        @param converterPath: ConverterPath
            The converter path to be used on Path objects to get the URL.
        @param extension: string
            The extension to use on the encoded paths.
        '''
        assert isinstance(scheme, str), 'Invalid scheme %s' % scheme
        assert isinstance(host, str), 'Invalid host %s' % host
        assert isinstance(root, str), 'Invalid root URI %s' % root
        assert isinstance(converterPath, ConverterPath), 'Invalid converter path %s' % converterPath
        assert extension is None or isinstance(extension, str), 'Invalid extension %s' % extension
        self.scheme = scheme
        self.host = host
        self.root = root
        self.converterPath = converterPath
        self.extension = extension

    def encode(self, path, parameters=None):
        '''
        @see: EncoderPath.encode
        '''
        assert isinstance(path, (Path, str)), 'Invalid path %s' % path
        if isinstance(path, Path):
            assert isinstance(path, Path)

            url = deque()
            url.append(self.root)
            url.append('/'.join(path.toPaths(self.converterPath)))
            if self.extension:
                url.append('.')
                url.append(self.extension)
            elif path.node.isGroup:
                url.append('/')

            query = urlencode(parameters) if parameters else ''
            return urlunsplit((self.scheme, self.host, quote(''.join(url)), query, ''))
        else:
            assert isinstance(path, str), 'Invalid path %s' % path
            if not path.strip().startswith('/'):
                # TODO: improve the relative path detection
                # This is an absolute path so we will return it as it is.
                return quote(path)
            # The path is relative to this server so we will convert it in an absolute path
            url = urlsplit(path)
            return urlunsplit((self.scheme, self.host, quote(url.path), url.query, url.fragment))
