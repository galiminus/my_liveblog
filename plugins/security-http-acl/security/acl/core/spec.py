'''
Created on Jan 21, 2013

@package: security acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Specifications for core access support.
'''

from ally.design.bean import Bean, Attribute
from security.acl.api.access import Access
import abc

# --------------------------------------------------------------------

class AclAccess(Access, Bean):
    '''
    Extends the model by providing also the markers within the access.
    '''
    markers = dict; markers = Attribute(markers, factory=dict, doc='''
    @rtype: dictionary{TypeProperty: string}
    The markers used in filters indexed by the property type.
    ''')

class IAclAccessService(metaclass=abc.ABCMeta):
    '''
    API for access model service.
    '''
    
    @abc.abstractmethod
    def rightsFor(self, *names, typeName=None):
        '''
        Provides the rights based on the provided filters.
        
        @param names: arguments[string|Iterable(string)]
            The right names to provide the rights for.
        @param typeName: string|None
            The type name to provide the rights for, if None then this method will not filter based on right type.
        @return: list[RightBase]
            The active rights based on the provided data.
        '''
    
    @abc.abstractmethod
    def accessFor(self, rights):
        '''
        Provides the access objects compiled for the provided right or rights.
        
        @param rights: Iterable(RightBase)|RightBase
            The rights to construct accesses for.
        @return: list[AclAccess]
            The list of access models reflecting the provided rights.
        '''
