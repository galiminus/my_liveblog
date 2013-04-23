'''
Created on Jan 25, 2013

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup patch when the server is run with ally core http.
'''

from ..ally_http import server_type
from .processor import dump_requests_size, dump_requests_path
from ally.container import ioc
from ally.design.processor import Handler
from ally.http.impl.processor.asyncore_content import AsyncoreContentHandler
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import ally_core_http
except ImportError: log.info('No REST core available thus skip the resources patching specific for asyncore')
else:
    ally_core_http = ally_core_http # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from ..ally_core.processor import assemblyResources, parser
    from ..ally_core_http.processor import updateAssemblyResourcesForHTTP

    @ioc.entity
    def asyncoreContent() -> Handler:
        b = AsyncoreContentHandler()
        b.dumpRequestsSize = dump_requests_size()
        b.dumpRequestsPath = dump_requests_path()
        return b
    
    # ----------------------------------------------------------------
    
    @ioc.after(updateAssemblyResourcesForHTTP)
    def updateAssemblyResourcesForHTTPAsyncore():
        if server_type() == 'asyncore':
            assemblyResources().add(asyncoreContent(), before=parser())
