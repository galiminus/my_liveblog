'''
Created on Jan 19, 2013

@package: support acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the ACL right that is designed for handling service based mapping.
'''

from acl.spec import RightBase, Filter
from ally.api.config import GET, INSERT, UPDATE, DELETE
from ally.api.operator.container import Service, Call
from ally.api.operator.type import TypeService
from ally.api.type import typeFor
from ally.core.impl.invoker import InvokerCall
from ally.core.impl.node import MatchProperty, NodeProperty
from ally.core.spec.resources import Invoker, Node, INodeChildListener, \
    INodeInvokerListener, Path
from ally.design.bean import Bean, Attribute
from ally.support.core.util_resources import iterateNodes, pathForNode, \
    METHOD_NODE_ATTRIBUTE, invokerCallOf
from collections import Iterable
from inspect import isfunction

# --------------------------------------------------------------------

class RightService(RightBase):
    '''
    The ACL right implementation designed for services.
    
    The filter policy is as follows:
        - if a call within a right has multiple representation and there is a filter for that call then only the call
          representation that can be filtered will be used.
        - if a call has a filter defined and is used in conjunction with a different right that doesn't have a filter for
          the same call then the unfiltered call is used, this way the right that allows more access wins.
    '''
    
    @classmethod
    def iterPermissions(cls, node, rights, method=None):
        '''
        @see: RightBase.iterPermissions
        '''
        assert isinstance(rights, Iterable), 'Invalid rights %s' % rights
        indexed = {}
        for right in rights:
            assert isinstance(right, RightService), 'Invalid right %s' % right
            cacheNode = right._process(node)
            assert isinstance(cacheNode, CacheNode)
            for structCall, cacheCall in cacheNode.calls.items():
                assert isinstance(structCall, StructCall)
                assert isinstance(cacheCall, CacheCall)
                
                if method:
                    assert isinstance(method, int), 'Invalid method %s' % method
                    if not method & structCall.call.method: continue
                assert isinstance(structCall.call, Call)
                
                # Processing invokers
                indexedServices = indexed.get(structCall.call.method)
                if indexedServices is None: indexedServices = indexed[structCall.call.method] = {}
                
                indexedCalls = indexedServices.get(structCall.serviceType)
                if indexedCalls is None: indexedCalls = indexedServices[structCall.serviceType] = {}
                
                invokersAndFilters = indexedCalls.get(structCall.call.name)
                if invokersAndFilters is None:
                    invokersAndFilters = indexedCalls[structCall.call.name] = ({}, {})
                    isFirst = True
                else: isFirst = False
                cacheInvokers, filters = invokersAndFilters
                cacheInvokers.update(cacheCall.invokers)
                
                # Processing filters
                if StructCall.filters in structCall:
                    if isFirst: filters.update(structCall.filters)
                    elif filters:  # Means there is something in the filters
                        oldFilters = dict(filters)
                        filters.clear()
                        for resourceType, structFilter in structCall.filters.items():
                            assert isinstance(structFilter, Filter)
                            resourceFilter = oldFilters.get(resourceType)
                            if not resourceFilter: continue
                            assert isinstance(resourceFilter, Filter)
                            
                            if resourceFilter.priority > structFilter.priority: filters[resourceType] = structFilter
                            else: filters[resourceType] = resourceFilter
                elif filters: filters.clear()  # Clear all the filters since this structure requires no filtering
        
        for indexedMethod, indexedServices in indexed.items():
            for indexedCalls in indexedServices.values():
                for cacheInvokers, filters in indexedCalls.values():
                    for cacheInvoker in cacheInvokers.values():
                        assert isinstance(cacheInvoker, CacheInvoker)
                        path = pathForNode(cacheInvoker.node)
                        assert isinstance(path, Path)
                        # We need to check if the returned node has at least one filter in the path.
                        # TODO: check implementation, since this was done in a hurry
                        available = []
                        for resourceType, filter in filters.items():
                            for match in path.matches:
                                if isinstance(match, MatchProperty):
                                    assert isinstance(match, MatchProperty)
                                    assert isinstance(match.node, NodeProperty)
                                    if resourceType in match.node.typesProperties:
                                        available.append(filter)
                                        break
                        yield indexedMethod, path, cacheInvoker.invoker, available
    
    def __init__(self, name, description, **keyargs):
        '''
        @see: RightBase.__init__
        '''
        super().__init__(name, description, **keyargs)
        self._struct = Structure()
        
    def hasPermissions(self, node, method=None):
        '''
        @see: RightBase.hasPermissions
        '''
        assert isinstance(node, Node), 'Invalid node %s' % node
        
        cacheNode = self._process(node)
        if not cacheNode.calls: return False
        
        if method is None: return True
        assert isinstance(method, int), 'Invalid method %s' % method
        
        for structCall in cacheNode.calls:
            assert isinstance(structCall, StructCall)
            if structCall.call.method == method: return True
        return False
    
    # ----------------------------------------------------------------
    
    def byName(self, service, *names, filter=None):
        '''
        Used for adding to the right the service calls.
        
        @param service: service type
            The service type to be used.
        @param names: arguments[string]
            The names of the service call to associate with the right.
        @param filter: Filter|None
            The filter to be used with the added calls, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        typ = typeFor(service)
        assert isinstance(typ, TypeService), 'Invalid service %s' % service
        assert names, 'At least a name is required'
        assert isinstance(typ.service, Service)
        for name in names:
            if isfunction(name): name = name.__name__
            assert name in typ.service.calls, 'Invalid call name \'%s\' for service %s' % (name, typ)
            call = typ.service.calls[name]
            assert isinstance(call, Call)
            structCall = self._obtainFor(typ, call)
            self._pushFilter(structCall, filter)
        return self
        
    def allFor(self, method, *services, filter=None):
        '''
        Used for adding to the right the service calls that have the specified method.
        
        @param method: integer
            The method or methods composed by using the | operator to be associated with the right.
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        assert isinstance(method, int), 'Invalid method %s' % method
        assert services, 'At least one service is required'
        
        for service in services:
            typ = typeFor(service)
            assert isinstance(typ, TypeService), 'Invalid service %s' % service
            
            assert isinstance(typ.service, Service)
            for call in typ.service.calls.values():
                assert isinstance(call, Call)
                if call.method & method:
                    structCall = self._obtainFor(typ, call)
                    self._pushFilter(structCall, filter)
        return self
                    
    def allGet(self, *services, filter=None):
        '''
        Used for adding to the right the service calls that are Get.
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(GET, *services, filter=filter)
        
    def allInsert(self, *services, filter=None):
        '''
        Used for adding to the right the service calls that are Insert.
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(INSERT, *services, filter=filter)
        
    def allUpdate(self, *services, filter=None):
        '''
        Used for adding to the right the service calls that are Update.
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(UPDATE, *services, filter=filter)
        
    def allDelete(self, *services, filter=None):
        '''
        Used for adding to the right the service calls that are Delete.
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(DELETE, *services, filter=filter)
        
    def allModify(self, *services, filter=None):
        '''
        Used for adding to the right the service calls that modify the data (Insert, Update, Delete).
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(INSERT | UPDATE | DELETE, *services, filter=filter)
        
    def all(self, *services, filter=None):
        '''
        Used for adding to the right all the service calls.
        
        @param service: arguments[service type]
            The services types to be used.
        @param filter: Filter|None
            The filter to be used with the added services, for more details about filter policy.
        @return: self
            The self object for chaining purposes.
        '''
        return self.allFor(GET | INSERT | UPDATE | DELETE, *services, filter=filter)
                    
    # ----------------------------------------------------------------
    
    def _obtainFor(self, service, call):
        '''
        Provides the structure call for the provided arguments.
        
        @return: StructCall
        '''
        assert isinstance(call, Call)
        structMethod = self._struct.methods.get(call.method)
        if not structMethod: structMethod = self._struct.methods[call.method] = StructMethod()
        structService = structMethod.services.get(service)
        if not structService: structService = structMethod.services[service] = StructService()
        structCall = structService.calls.get(call.name)
        if not structCall: structCall = structService.calls[call.name] = StructCall(service, call)
        return structCall
    
    def _pushFilter(self, structCall, filter):
        '''
        Pushes the filter on the provided structure call. Read the filter policy of the right definition.
        '''
        if filter:
            assert isinstance(filter, Filter), 'Invalid filter %s' % filter
            filterOld = structCall.filters.get(filter.resource)
            if filterOld:
                assert isinstance(filterOld, Filter), 'Invalid filter %s' % filterOld
                if filter.priority > filterOld.priority: structCall.filters[filter.resource] = filter
            else: structCall.filters[filter.resource] = filter
            
    def _process(self, root):
        '''
        Process the cache for the node.
        
        @return: CacheNode
        '''
        assert isinstance(root, Node), 'Invalid node %s' % root
        cacheNode = self._struct.cacheNodes.get(CacheNode.idFor(root))
        if cacheNode: return cacheNode
        
        cacheNode = CacheNode(self._struct, root)
        for node in iterateNodes(root):
            assert isinstance(node, Node), 'Invalid node %s' % node

            for method, attr in METHOD_NODE_ATTRIBUTE.items():
                original = getattr(node, attr)
                if not original:  continue
                invoker = invokerCallOf(original)
                if not invoker:  continue
                
                assert isinstance(invoker, InvokerCall)
                assert isinstance(invoker.call, Call)
                
                structMethod = self._struct.methods.get(method)
                if not structMethod: continue
                assert isinstance(structMethod, StructMethod)
                
                structService = structMethod.services.get(typeFor(invoker.implementation))
                if not structService: continue
                assert isinstance(structService, StructService)
                
                structCall = structService.calls.get(invoker.call.name)
                if not structCall: continue
                assert isinstance(structCall, StructCall)
                
                cacheCall = cacheNode.calls.get(structCall)
                if not cacheCall: cacheCall = cacheNode.calls[structCall] = CacheCall()
                
                nodeId = id(node)
                cacheInvoker = cacheCall.invokers.get(nodeId)
                if not cacheInvoker: cacheCall.invokers[nodeId] = CacheInvoker(invoker=original, node=node)
        return cacheNode
    
# --------------------------------------------------------------------

class Structure(Bean):
    '''
    The structure root.
    '''
    
    methods = dict; methods = Attribute(methods, factory=dict, doc='''
    @rtype: dictionary{integer, StructMethod)
    The method structure indexed by method.
    ''')
    cacheNodes = dict; cacheNodes = Attribute(cacheNodes, factory=dict, doc='''
    @rtype: dictionary{Node, CacheNode)
    The node caches indexed by the root node.
    ''')

class StructMethod(Bean):
    '''
    The structure for method.
    '''
    
    services = dict; services = Attribute(services, factory=dict, doc='''
    @rtype: dictionary{TypeService, StructService}
    The service structure indexed by service types.
    ''')
    
class StructService(Bean):
    '''
    The structure for service.
    '''
    
    calls = dict; calls = Attribute(calls, factory=dict, doc='''
    @rtype: dictionary{string, StructCall}
    The call structure indexed by call name.
    ''')
    
class StructCall(Bean):
    '''
    The cache for call.
    '''
    
    serviceType = TypeService; serviceType = Attribute(serviceType, doc='''
    @rtype: TypeService
    The service type of the structure call.
    ''')
    call = Call; call = Attribute(call, doc='''
    @rtype: Call
    The call of the structure.
    ''')
    filters = dict; filters = Attribute(filters, factory=dict, doc='''
    @rtype: dictionary{TypeProperty: Filter}
    The Filter indexed by the filtered resource type for the call.
    ''')
    
    def __init__(self, serviceType, call):
        assert isinstance(serviceType, TypeService), 'Invalid service type %s' % serviceType
        assert isinstance(call, Call), 'Invalid call %s' % call
        super().__init__(serviceType=serviceType, call=call)

class CacheNode(Bean, INodeChildListener, INodeInvokerListener):
    '''
    The cache for node.
    '''
    
    structure = Structure; structure = Attribute(structure, doc='''
    @rtype: Structure
    The structure that the cache node belongs to.
    ''')
    root = Node; root = Attribute(root, doc='''
    @rtype: Node
    The root node that this cache represents.
    ''')
    calls = dict; calls = Attribute(calls, factory=dict, doc='''
    @rtype: dictionary{StructCall, CacheCall}
    The call caches indexed by the structure call.
    ''')
    
    @classmethod
    def idFor(cls, root):
        ''' Provides the id for the root node.'''
        return id(root)
    
    def __init__(self, structure, root):
        assert isinstance(structure, Structure), 'Invalid structure %s' % structure
        assert isinstance(root, Node), 'Invalid root node %s' % root
        super().__init__(structure=structure, root=root)
        self.id = self.idFor(root)
        structure.cacheNodes[self.id] = self
        root.addStructureListener(self)
    
    # ----------------------------------------------------------------
    
    def onChildAdded(self, node, child):
        '''
        @see: INodeChildListener.onChildAdded
        '''
        del self.structure.cacheNodes[self.id]
    
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        del self.structure.cacheNodes[self.id]

class CacheCall(Bean):
    '''
    The cache for call.
    '''
    
    invokers = dict; invokers = Attribute(invokers, factory=dict, doc='''
    @rtype: dictionary{integer, CacheInvoker}
    The invoker caches indexed by the node id.
    ''')       
    
class CacheInvoker(Bean):
    '''
    The cache for invoker.
    '''

    invoker = Invoker; invoker = Attribute(invoker, doc='''
    @rtype: Invoker
    The invoker.
    ''')
    node = Node; node = Attribute(node, doc='''
    @rtype: Node
    The invoker node.
    ''')
