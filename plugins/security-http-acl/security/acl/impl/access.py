'''
Created on Jan 16, 2013

@package: security acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for access specifications.
'''

from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.exception import InputError
from security.acl.api.access import IAccessService
from security.acl.core.spec import IAclAccessService
from security.api.right import IRightService, Right
from security.api.right_type import IRightTypeService, RightType

# --------------------------------------------------------------------

@injected
@setup(IAccessService, name='accessService')
class AccessService(IAccessService):
    '''
    Implementation for @see: IAccessService.
    '''
    
    aclAccessService = IAclAccessService; wire.entity('aclAccessService')
    # The acl access service.
    rightTypeService = IRightTypeService; wire.entity('rightTypeService')
    # The right type service.
    rightService = IRightService; wire.entity('rightService')
    # The right service.
    
    def __init__(self):
        assert isinstance(self.aclAccessService, IAclAccessService), 'Invalid acl access service %s' % self.aclAccessService
        assert isinstance(self.rightTypeService, IRightTypeService), 'Invalid right type service %s' % self.rightTypeService
        assert isinstance(self.rightService, IRightService), 'Invalid right service %s' % self.rightService
        
    def getAccessById(self, id):
        '''
        IAccessService.getAccessById
        '''
        right = self.rightService.getById(id)
        assert isinstance(right, Right)
        rightType = self.rightTypeService.getById(right.Type)
        assert isinstance(rightType, RightType)
        
        rights = self.aclAccessService.rightsFor(right.Name, typeName=rightType.Name)
        if not rights: raise InputError('No access available for right')
        return self.aclAccessService.accessFor(rights)
