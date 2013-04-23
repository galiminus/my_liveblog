'''
Created on Jan 21, 2013

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the setups for populating default data.
'''

from ..acl.acl import acl
from __setup__.ally_core.resources import resourcesRoot
from acl.spec import TypeAcl, RightBase
from ally.container import support
from ally.exception import InputError
from distribution.container import app
from security.api.right import IRightService, Right
from security.api.right_type import IRightTypeService, RightType

# --------------------------------------------------------------------

@app.analyze
def populateRights():
    '''
    Synchronize the active acl rights with the database rights.
    '''
    rightTypeService = support.entityFor(IRightTypeService)
    assert isinstance(rightTypeService, IRightTypeService)
    rightService = support.entityFor(IRightService)
    assert isinstance(rightService, IRightService)
    for aclType in acl().activeTypes(resourcesRoot()):
        assert isinstance(aclType, TypeAcl), 'Invalid acl type %s' % aclType
        
        try: rightType = rightTypeService.getByName(aclType.name)
        except InputError:
            rightType = RightType()
            rightType.Name = aclType.name
            rightType.Description = aclType.description
            rightTypeId = rightTypeService.insert(rightType)
        else:
            # Update the description if is the case
            assert isinstance(rightType, RightType)
            if rightType.Description != aclType.description:
                rightType.Description = aclType.description
                rightTypeService.update(rightType)
            rightTypeId = rightType.Id
        
        aclRights = {right.name: right for right in aclType.activeRights(resourcesRoot())}
        for right in rightService.getAll(rightTypeId):
            assert isinstance(right, Right), 'Invalid right %s' % right
        
            aclRight = aclRights.pop(right.Name, None)
            if aclRight:
                assert isinstance(aclRight, RightBase)
                # Update the description if is the case
                if right.Description != aclRight.description:
                    right.Description = aclRight.description
                    rightService.update(right)
        
        for aclRight in aclRights.values():
            right = Right()
            right.Type = rightTypeId
            right.Name = aclRight.name
            right.Description = aclRight.description
            rightService.insert(right)
