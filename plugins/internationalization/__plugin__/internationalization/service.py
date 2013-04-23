'''
Created on Jan 9, 2012

@package: internationalization
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services setup for internationalization.
'''

from ..cdm.local_cdm import contentDeliveryManager
from ..plugin.registry import addService
from .db_internationalization import bindInternationalizationSession, \
    bindInternationalizationValidations
from ally.container import support, ioc
from cdm.spec import ICDM
from cdm.support import ExtendPathCDM
from internationalization.scanner import Scanner

# --------------------------------------------------------------------

SERVICES = 'internationalization.api.**.I*Service'

support.createEntitySetup('internationalization.impl.**.*')
support.createEntitySetup('internationalization.*.impl.**.*')
support.createEntitySetup(Scanner)
support.bindToEntities('internationalization.impl.**.*Alchemy', binders=bindInternationalizationSession)
support.listenToEntities(SERVICES, listeners=addService(bindInternationalizationValidations), beforeBinding=False)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def cdmLocale() -> ICDM:
    '''
    The content delivery manager (CDM) for the locale files.
    '''
    return ExtendPathCDM(contentDeliveryManager(), 'cache/locale/%s')
