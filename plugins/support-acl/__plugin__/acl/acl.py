'''
Created on Jan 15, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the acl setup.
'''

from acl.impl.sevice_right import RightService
from acl.spec import Acl, TypeAcl
from ally.container import ioc
from ally.internationalization import NC_

# --------------------------------------------------------------------

def aclRight(name, description) -> RightService: return RightService(name, description, type=aclType())

# --------------------------------------------------------------------

@ioc.entity
def acl() -> Acl: return Acl()

@ioc.entity
def aclType() -> TypeAcl:
    return TypeAcl(NC_('security', 'Access control layer'), NC_('security',
    'Right type for the basic access control layer right setups'))

# --------------------------------------------------------------------

setup = ioc.before(acl)

# --------------------------------------------------------------------

@setup
def registerAclType():
    acl().add(aclType())
