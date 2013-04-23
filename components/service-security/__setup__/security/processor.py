'''
Created on Jan 5, 2012

@package: security service
@copyright: 2012 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl - 3.0.txt
@author: Gabriel Nistor

The setup for the security service.
'''

from ..ally_core_http.support_ajax import headerSetAjax
from ..ally_core_http.support_nocache import headerSetNoCache
from ..ally_http.processor import contentLengthEncode, contentTypeEncode, header, \
    internalError
from ..ally_http.server import pathAssemblies
from ally.container import ioc
from ally.container.error import ConfigError
from ally.design.processor import Handler, Assembly
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@ioc.config
def server_provide_security():
    ''' Flag indicating that this server should provide the security service'''
    return True

@ioc.config
def server_pattern_security():
    ''' The pattern used for matching the secured resources paths in HTTP URL's'''
    return '^resources\/my(/|(?=\\.)|$)'

@ioc.config
def access_headers():
    '''
    The headers used in getting the access data, by default provides the JSON encoding using UTF-8, if you change the
    charset encoding please also change the "access_response_encoding" configuration accordingly
    '''
    return {
            'Host': 'security',
            'Content-Type': 'text/json;charset=UTF-8'
            }

@ioc.config
def access_uri_root() -> str:
    ''' The root URI of the access URI'''
    raise ConfigError('There is no access URI root provided')

@ioc.config
def access_uri() -> str:
    '''
    The access URI to fetch the Access objects from, this URI needs to have a marker '*' where the actual authentication
    code will be placed, also this URI needs to return json encoded Access objects'''
    raise ConfigError('There is no access URI provided')

@ioc.config
def access_response_encoding():
    ''' The encoding for the JSON response, attention this is made based on the access headers'''
    return 'UTF-8'
    
@ioc.config
def access_parameters():
    ''' The list of parameters to use for the access call'''
    return []

@ioc.config
def cleanup_inactive_auth_timeout():
    ''' The number of seconds of inactivity of an authenticated access after which the cached access is cleared.'''
    return 60

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def assemblyRequest() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing the security service requests.
    '''
    return Assembly()

@ioc.entity
def assemblySecurity() -> Assembly:
    '''
    The assembly containing the security handlers..
    '''
    return Assembly()

@ioc.entity
def security() -> Handler:
    #TODO: remove this ugly patch, the problem it seems is that the security root package 'security' is used also by a plugin
    # if loaded from eggs because the components are loaded before the plugins it creates problems for the loader, this problem
    # will go away when the service-security becomes service-gateway. As a general root, never ever have components use the
    # same package root as the plugins.
    from security.core.http.impl.processor.security import SecurityHandler
    b = SecurityHandler()
    b.requestAssembly = assemblyRequest()
    b.accessHeaders = access_headers()
    b.accessUriRoot = access_uri_root()
    b.accessUri = access_uri()
    b.accessParameters = access_parameters()
    b.accessResponseEncoding = access_response_encoding()
    b.cleanupTimeout = cleanup_inactive_auth_timeout()
    return b

# --------------------------------------------------------------------

@ioc.before(assemblySecurity)
def updateAssemblySecurity():
    assemblySecurity().add(internalError(), header(), security(), headerSetAjax(), headerSetNoCache(),
                           contentTypeEncode(), contentLengthEncode())

# --------------------------------------------------------------------

try: from .. import ally_core_http
except ImportError: log.info('No REST core available, you need to configure an external request assembly for processing')
else: 
    ally_core_http = ally_core_http  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from ..ally_core.processor import assemblyResources
    from ..ally_core_http.processor import updatePathAssembliesForResources
    
    @ioc.before(assemblyRequest)
    def updateAssemblyResourcesAuthentication():
        assemblyRequest().add(assemblyResources())

    @ioc.before(updatePathAssembliesForResources)
    def updatePathAssembliesForContent():
        # We need to register the security pattern before the REST pattern since the security 
        # is an extension of the REST pattern
        if server_provide_security(): pathAssemblies().append((server_pattern_security(), assemblySecurity()))
