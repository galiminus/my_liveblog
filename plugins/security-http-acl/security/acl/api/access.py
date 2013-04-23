'''
Created on Jan 12, 2013

@package: security acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

API specifications for security gateway.
'''

from ally.api.config import service, call
from ally.api.type import List, Iter
from security.api.domain_security import modelSecurity
from security.api.right import Right

# --------------------------------------------------------------------

@modelSecurity
class Access:
    '''
    Provides the path model. The pattern is a regex that allows the path to be checked if valid.
    Examples:
    Lets consider the access
        Pattern = "\/HR\/User\/([0-9\-]+)\/Resource\/([0-9\-]+)"
        Method = ["GET"]
        Filter = ["/Authenticated/1/User/*/IsAuthenticated", ""]
        
    The validates should be empty because in our case the received user id is actually the authenticated id and we can
    use that internally but this is just to provide an example how the validate URL will look like if the user id is
    not authenticated. 
    
    We have a URL: http://localhost/resources/User/1/Resource/2
    
    First the Pattern is checked if is valid and we get a match we isolate all the capturing groups data, in this case
    the groups will be ("1", "2").
    
    In case of GET or DELETE the Filter is used, for every group there has to be a filter entry.
    '''
    Pattern = str
    Methods = List(str)
    Secured = str
    Pattern = str
    Filter = List(str)

# --------------------------------------------------------------------

# No query

# --------------------------------------------------------------------

@service
class IAccessService:
    '''
    The access service.
    '''
    
    @call
    def getAccessById(self, id:Right.Id) -> Iter(Access):
        '''
        Get the accesses for the provided right id.
        '''
