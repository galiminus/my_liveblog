'''
Created on Jan 20, 2013

@package: GUI security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ACL GUI right.
'''

from acl.impl.sevice_right import RightService
from acl.spec import TypeAcl
from collections import Iterable
from gui.action.api.action import Action

# --------------------------------------------------------------------

class RightAction(RightService):
    '''
    The model that describes a right that is binded with actions.
    @see: RightService
    '''
    
    @classmethod
    def iterPermissions(cls, node, rights, method=None):
        '''
        @see: RightService.iterPermissions
        '''
        assert isinstance(rights, Iterable), 'Invalid rights %s' % rights
        rights = list(rights)
        types = {right.type().name: right.type() for right in rights}
        for aType in types.values():
            assert isinstance(aType, TypeAction)
            rights.append(aType.default())
        return super(RightAction, cls).iterPermissions(node, rights, method=method)
    
    def __init__(self, name, description, type, **keyargs):
        '''
        @see: RightBase.__init__
        '''
        super().__init__(name, description, type=type, **keyargs)
        assert isinstance(type, TypeAction), 'Invalid type %s' % type
        self._actions = []
        self._type = type
        
    def type(self):
        '''
        Provides the action type.
        '''
        return self._type
        
    def actions(self):
        '''
        Provides an iterator over the actions of the right.
        '''
        return iter(self._actions)
        
    def addActions(self, *actions):
        '''
        Add a new action to the right action.
        
        @param action: Action
            The action to be added.
        @return: self
            The self object for chaining purposes.
        '''
        for action in actions:
            assert isinstance(action, Action), 'Invalid action %s' % action
            self._actions.append(action)
        return self

class RightActionDefault(RightService):
    '''
    Provides the default action right, usually only one per type.
    @see: RightService
    '''
    
    def __init__(self):
        '''
        Construct the right action defaults.
        '''
        super().__init__('', '')
    
    def hasPermissions(self, node, method=None):
        '''
        @see: RightService.hasPermissions
        '''
        return False

class TypeAction(TypeAcl):
    '''
    Type specific action.
    @see: TypeAcl
    '''
    
    def __init__(self, name, description, **keyargs):
        '''
        Construct the action type.
        '''
        super().__init__(name, description, **keyargs)
        self._default = RightActionDefault()
        
    def default(self):
        '''
        Provides the default right.
        '''
        return self._default
        
