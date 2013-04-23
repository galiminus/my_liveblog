'''
Created on Jan 15, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the acl setup.
'''

from ..acl import acl
from acl.impl.action_right import RightAction, TypeAction
from ally.container import ioc
from ally.internationalization import NC_
from gui.action.api.action import IActionManagerService

# --------------------------------------------------------------------

def actionRight(name, description) -> RightAction: return RightAction(name, description, type=aclType())

# --------------------------------------------------------------------

@ioc.entity
def aclType() -> TypeAction:
    return TypeAction(NC_('security', 'GUI based access control layer'), NC_('security',
    'Right type for the graphical user interface based access control layer right setups'))

# --------------------------------------------------------------------

setup = acl.setup

# --------------------------------------------------------------------

@setup
def registerAclType():
    acl.acl().add(aclType())

@setup
def updateDefaults():
    aclType().default().allGet(IActionManagerService)
