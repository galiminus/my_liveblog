'''
Created on Jan 9, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for security.
'''
    
from ..plugin.registry import addService
from .db_security import bindSecuritySession, bindSecurityValidations
from ally.container import support

# --------------------------------------------------------------------

SERVICES = 'security.api.**.I*Service', 'security.**.api.**.I*Service'

support.createEntitySetup('security.impl.**.*', 'security.**.impl.**.*')
support.bindToEntities('security.impl.**.*Alchemy', 'security.**.impl.**.*Alchemy', binders=bindSecuritySession)
support.listenToEntities(*SERVICES, listeners=addService(bindSecuritySession, bindSecurityValidations))
support.loadAllEntities(*SERVICES)
