'''
Created on Nov 23, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the Mongrel2 web server plugins patch for the cdm.
'''

from ally.container import ioc, support
from __setup__.ally_http import server_type
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

try: from .. import cdm
except ImportError: log.info('No local CDM service to provide specific setup for mongrel2 server')
else:
    cdm = cdm  # Just to avoid the import warning
    # ----------------------------------------------------------------
    
    from ..cdm.local_cdm import use_linked_cdm
    
    ioc.doc(use_linked_cdm, '''
    !!!Attention, if the mongrel2 server is selected this option will always be "false"
    ''')
    
    @ioc.before(use_linked_cdm, auto=False)
    def use_linked_cdm_force():
        if server_type() == 'mongrel2': support.force(use_linked_cdm, False)

