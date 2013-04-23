'''
Created on Nov 24, 2011

@package: ally core http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from ..ally_core.encoder_decoder import parsingAssembly
from ..ally_core.processor import argumentsBuild, argumentsPrepare, \
    assemblyResources, updateAssemblyResources, createEncoder, renderEncoder, \
    explainError, methodInvoker, invoking, parser, default_characterset
from ..ally_core.resources import resourcesRoot
from ..ally_http.processor import header, contentTypeDecode, contentLengthDecode, \
    contentTypeEncode, contentLengthEncode
from ..ally_http.server import pathAssemblies
from ally.container import ioc
from ally.core.http.impl.processor.encoder import CreateEncoderPathHandler
from ally.core.http.impl.processor.fetcher import FetcherHandler
from ally.core.http.impl.processor.headers.accept import AcceptDecodeHandler
from ally.core.http.impl.processor.headers.allow import AllowEncodeHandler
from ally.core.http.impl.processor.headers.content_disposition import \
    ContentDispositionDecodeHandler
from ally.core.http.impl.processor.headers.content_language import \
    ContentLanguageDecodeHandler, ContentLanguageEncodeHandler
from ally.core.http.impl.processor.internal_error import \
    InternalDevelErrorHandler
from ally.core.http.impl.processor.method import MethodHandler
from ally.core.http.impl.processor.parameter import ParameterHandler
from ally.core.http.impl.processor.parsing_multipart import \
    ParsingMultiPartHandler
from ally.core.http.impl.processor.redirect import RedirectHandler
from ally.core.http.impl.processor.uri import URIHandler
from ally.core.spec.resources import ConverterPath
from ally.design.processor import Handler, Assembly

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def server_pattern_rest():
    ''' The pattern used for matching the REST resources paths in HTTP URL's'''
    return '^resources(/|(?=\\.)|$)'

@ioc.config
def read_from_params():
    '''If true will also read header values that are provided as query parameters'''
    return True

@ioc.config
def allow_method_override():
    '''
    If true will allow the method override by using the header 'X-HTTP-Method-Override', the GET can be override with
    DELETE and the POST with PUT.
    '''
    return True

# --------------------------------------------------------------------

@ioc.entity
def converterPath() -> ConverterPath: return ConverterPath()

# --------------------------------------------------------------------
# Header decoders

@ioc.entity
def internalDevelError() -> Handler: return InternalDevelErrorHandler()

@ioc.entity
def contentDispositionDecode() -> Handler: return ContentDispositionDecodeHandler()

@ioc.entity
def contentLanguageDecode() -> Handler: return ContentLanguageDecodeHandler()

@ioc.entity
def acceptDecode() -> Handler: return AcceptDecodeHandler()

@ioc.entity
def method() -> Handler: return MethodHandler()

# --------------------------------------------------------------------
# Header encoders

@ioc.entity
def contentLanguageEncode() -> Handler: return ContentLanguageEncodeHandler()

@ioc.entity
def allowEncode() -> Handler: return AllowEncodeHandler()

# --------------------------------------------------------------------

@ioc.entity
def uri() -> Handler:
    b = URIHandler()
    b.resourcesRoot = resourcesRoot()
    b.converterPath = converterPath()
    return b

@ioc.entity
def parameter() -> Handler: return ParameterHandler()

@ioc.entity
def fetcher() -> Handler: return FetcherHandler()

@ioc.replace(createEncoder)
def createEncoderPath() -> Handler: return CreateEncoderPathHandler()

@ioc.replace(parser)
def parserMultiPart() -> Handler:
    b = ParsingMultiPartHandler()
    b.charSetDefault = default_characterset()
    b.parsingAssembly = parsingAssembly()
    b.populateAssembly = assemblyMultiPartPopulate()
    return b

@ioc.entity
def redirect() -> Handler:
    b = RedirectHandler()
    b.redirectAssembly = assemblyRedirect()
    return b

# --------------------------------------------------------------------

@ioc.entity
def assemblyMultiPartPopulate() -> Assembly:
    '''
    The assembly containing the handlers that will populate data on the next request content.
    '''
    return Assembly()

@ioc.entity
def assemblyRedirect() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing a redirect.
    '''
    return Assembly()

# --------------------------------------------------------------------

@ioc.before(pathAssemblies)
def updatePathAssembliesForResources():
    pathAssemblies().append((server_pattern_rest(), assemblyResources()))

@ioc.after(updateAssemblyResources)
def updateAssemblyResourcesForHTTP():
    assemblyResources().add(internalDevelError(), before=argumentsPrepare())
    assemblyResources().add(header(), uri(), before=methodInvoker())

    assemblyResources().add(redirect(), contentTypeDecode(), contentLengthDecode(), contentLanguageDecode(),
                            acceptDecode(), after=methodInvoker())

    assemblyResources().add(parameter(), fetcher(), before=argumentsBuild())

    assemblyResources().add(contentTypeEncode(), contentLanguageEncode(), allowEncode(), after=renderEncoder())
    assemblyResources().add(contentLengthEncode(), after=explainError())

    if allow_method_override(): assemblyResources().add(method(), before=uri())

@ioc.before(assemblyMultiPartPopulate)
def updateAssemblyMultiPartPopulate():
    assemblyMultiPartPopulate().add(header(), contentTypeDecode(), contentDispositionDecode())

@ioc.before(assemblyRedirect)
def updateAssemblyRedirect():
    assemblyRedirect().add(argumentsBuild(), invoking())
