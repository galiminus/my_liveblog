'''
Created on Jan 21, 2013

@package: security acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Implementation for the ACL access service.
'''

from ..spec import IAclAccessService
from acl.spec import Acl, RightBase, Filter, TypeAcl
from ally.api.config import GET, DELETE, INSERT, UPDATE
from ally.api.operator.container import Model
from ally.api.operator.type import TypeService, TypeProperty
from ally.api.type import typeFor
from ally.container import wire
from ally.container.ioc import injected
from ally.container.support import setup
from ally.core.spec.resources import Node, ConverterPath, Path, \
    INodeChildListener, INodeInvokerListener, Invoker
from ally.http.spec.server import METHOD_GET, METHOD_DELETE, METHOD_POST, \
    METHOD_PUT
from ally.support.core.util_resources import findNodesFor, pathForNode, \
    propertyTypesOf, ReplacerWithMarkers
from collections import Iterable
from security.acl.api.filter import IAclFilter
from security.acl.core.spec import AclAccess
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

@injected
@setup(IAclAccessService, name='aclAccessService')
class AclAccessService(IAclAccessService, INodeChildListener, INodeInvokerListener):
    '''
    Implementation for @see: IAclAccessService
    '''
    
    acl = Acl; wire.entity('acl')
    # The acl repository.
    resourcesRoot = Node; wire.entity('resourcesRoot')
    # The root node to process the security rights repository against.
    converterPath = ConverterPath; wire.entity('converterPath')
    # The converter path to be used.
    
    def __init__(self):
        '''
        Construct the access service.
        '''
        assert isinstance(self.acl, Acl), 'Invalid acl repository %s' % self.acl
        assert isinstance(self.resourcesRoot, Node), 'Invalid root node %s' % self.resourcesRoot
        assert isinstance(self.converterPath, ConverterPath), 'Invalid converter path %s' % self.converterPath
        
        self._cacheFilters = {}
        self.resourcesRoot.addStructureListener(self)
        
    def rightsFor(self, *names, typeName=None):
        '''
        @see: IAclAccessService.rightsFor
        '''
        if names:
            aclNames = set()
            for name in names:
                if isinstance(name, str): aclNames.add(name)
                assert isinstance(name, Iterable), 'Invalid name %s' % name
                aclNames.update(name)
            if not aclNames: return []
        else: aclNames = None
        
        aclTypes, rights = self.acl.activeTypes(self.resourcesRoot), []
        if typeName is not None:
            assert isinstance(typeName, str), 'Invalid type name %s' % typeName
            aclTypes = (aclType for aclType in aclTypes if aclType.name == typeName)
        for aclType in aclTypes:
            assert isinstance(aclType, TypeAcl)
            if aclNames is not None:
                for right in aclType.activeRights(self.resourcesRoot):
                    assert isinstance(right, RightBase)
                    if right.name in aclNames: rights.append(right)
            else: rights.extend(aclType.activeRights(self.resourcesRoot))
            
        return rights
        
    def accessFor(self, rights):
        '''
        @see: IAclAccessService.accessFor
        '''
        if isinstance(rights, RightBase): rights = (rights,)
        assert isinstance(rights, Iterable), 'Invalid rights %s' % rights
        
        accesses, accessesGetByPattern, replacer = [], {}, ReplacerWithMarkers()
        # Process GET and OPTIONS access
        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, GET):
            assert isinstance(path, Path)
            
            filtersWithPath = self._processFilters(filters, replacer)
            data = self._processPatternWithFilters(path, invoker, filtersWithPath, replacer)
            
            access = AclAccess()
            access.Methods = [METHOD_GET]
            access.Pattern, access.Filter, accessMarkers = data
            if accessMarkers: access.markers.update(accessMarkers)
            
            accessesGetByPattern[access.Pattern] = access
            accesses.append(access)
        
        # Process DELETE access
        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, DELETE):
            assert isinstance(path, Path)
            
            filtersWithPath = self._processFilters(filters, replacer)
            data = self._processPatternWithFilters(path, invoker, filtersWithPath, replacer)
            
            pattern, accessFilters, accessMarkers = data
            
            access = accessesGetByPattern.get(pattern)
            if access and access.Filter == accessFilters:
                access.Methods.append(METHOD_DELETE)
                continue
            
            access = AclAccess()
            access.Methods = [METHOD_DELETE, METHOD_GET]  # Needed to add get also because of the method overide
            access.Pattern = pattern
            access.Filter = accessFilters
            if accessMarkers: access.markers.update(accessMarkers)
            
            accesses.append(access)
        
        # TODO: properly implement the secured redirect
        accessesUpdateByPattern = {}
        # Process POST access
        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, INSERT):
            assert isinstance(path, Path)
            
            filtersWithPath = self._processFilters(filters, replacer)
            data = self._processPatternWithFilters(path, invoker, filtersWithPath, replacer)
            
            access = AclAccess()
            access.Methods = [METHOD_POST]
            access.Pattern, access.Filter, accessMarkers = data
            if accessMarkers: access.markers.update(accessMarkers)
            
            accessesUpdateByPattern[access.Pattern] = access
            accesses.append(access)
            
        # Process PUT access
        for _method, path, invoker, filters in RightBase.iterPermissions(self.resourcesRoot, rights, UPDATE):
            assert isinstance(path, Path)
            
            filtersWithPath = self._processFilters(filters, replacer)
            data = self._processPatternWithFilters(path, invoker, filtersWithPath, replacer)
            
            pattern, accessFilters, accessMarkers = data
            
            access = accessesUpdateByPattern.get(pattern)
            if access and access.Filter == accessFilters:
                access.Methods.append(METHOD_PUT)
                continue
            
            access = AclAccess()
            access.Methods = [METHOD_PUT, METHOD_POST]  # Needed to add get also because of the method overide
            access.Pattern = pattern
            access.Filter = accessFilters
            if accessMarkers: access.markers.update(accessMarkers)
            
            accesses.append(access)
        
        accesses.sort(key=lambda access: (access.Pattern, access.Methods))
        return accesses
    
    # ----------------------------------------------------------------
    
    def onChildAdded(self, node, child):
        '''
        @see: INodeChildListener.onChildAdded
        '''
        self._cacheFilters.clear()
    
    def onInvokerChange(self, node, old, new):
        '''
        @see: INodeInvokerListener.onInvokerChange
        '''
        self._cacheFilters.clear()
        
    # ----------------------------------------------------------------
    
    def _processPatternWithSecured(self, path, invoker, replacer):
        '''
        Process the access pattern for secured by using the path and replacer.
        
        @param path: Path
            The path to process the pattern based on.
        @param invoker: Invoker
            The invoker to process the pattern based on.
        @param replacer: PatternReplacer
            The replacer to use on the path.
        @return: string
            It returns the pattern
        '''
        assert isinstance(path, Path), 'Invalid path %s' % path
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        replaceMarkers = []
        for propertyType in propertyTypesOf(path, invoker):
            assert isinstance(propertyType, TypeProperty), 'Invalid property type %s' % propertyType
            
            if propertyType.isOf(int): replaceMarkers.append('[0-9\\-]+')
            elif propertyType.isOf(str): replaceMarkers.append('[^\\/]+')
            else: raise Exception('Unusable type \'%s\'' % propertyType)
        
        replacer.register(replaceMarkers)
        pattern = ''.join(('\\/'.join(path.toPaths(self.converterPath, replacer)), '[\\/]?(?:\\.|$)'))
        return pattern
    
    def _processPatternWithFilters(self, path, invoker, filtersWithPath, replacer):
        '''
        Process the access pattern for filters by using the path and replacer.
        
        @param path: Path
            The path to process the pattern based on.
        @param invoker: Invoker
            The invoker to process the pattern based on.
        @param filtersWithPath: dictionary{TypeProperty, tuple(string, dictionary{TypeProperty: string}}
            A dictionary containing {resource type, (marked path, {authenticated type: marker}}
        @param replacer: PatternReplacer
            The replacer to use on the path.
        @return: tuple(string, list[string]|None, dictionary{TypeProperty: string}|None)
            Basically it returns the (pattern, filters if available, markers if available)
        '''
        assert isinstance(path, Path), 'Invalid path %s' % path
        assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        filters, markers, replaceMarkers = None, None, []
        for propertyType in propertyTypesOf(path, invoker):
            assert isinstance(propertyType, TypeProperty), 'Invalid property type %s' % propertyType
            pathAndMarkers = filtersWithPath.get(propertyType)
            if pathAndMarkers:
                filter, markers = pathAndMarkers
                if filters is None: filters = [filter]
                else: filters.append(filter)
                if markers is None: markers = dict(markers)
                else: markers.update(markers)
                isFiltered = True
            else: isFiltered = False
            
            if propertyType.isOf(int): replaceMarkers.append('([0-9\\-]+)' if isFiltered else '[0-9\\-]+')
            elif propertyType.isOf(str): replaceMarkers.append('([^\\/]+)' if isFiltered else '[^\\/]+')
            else: raise Exception('Unusable type \'%s\'' % propertyType)
        
        replacer.register(replaceMarkers)
        pattern = ''.join(('\\/'.join(path.toPaths(self.converterPath, replacer)), '[\\/]?(?:\\.|$)'))
        return pattern, filters, markers
    
    def _processFilters(self, filters, replacer):
        '''
        Process the filters into path filters.
        
        @param filters: Iterable(Filter)
            The filters to process.
        @param replacer: PatternReplacer
            The replacer to use on the path.
        @return: dictionary{TypeProperty, tuple(string, dictionary{TypeProperty: string}}
            A dictionary containing {resource type, (marked path, {authenticated type: marker}}
        '''
        assert isinstance(filters, Iterable), 'Invalid filters %s' % filter
        assert isinstance(replacer, ReplacerWithMarkers), 'Invalid replacer %s' % replacer
        
        filtersWithPath = {}
        for resourceFilter in filters:
            assert isinstance(resourceFilter, Filter), 'Invalid filter %s' % filter
            assert isinstance(resourceFilter.filter, IAclFilter), \
            'Invalid filter object %s for resource filter %s' % (resourceFilter.filter, resourceFilter)
            typeService = typeFor(resourceFilter.filter)
            assert isinstance(typeService, TypeService), \
            'Invalid filter %s, it needs to be mapped as a REST service' % resourceFilter.filter
            pathAndMarkers = self._cacheFilters.get(typeService)
            if not pathAndMarkers:
                nodes = findNodesFor(self.resourcesRoot, typeService, 'isAllowed')
                if not nodes:
                    log.error('The filter service %s cannot be located in the resources tree', typeService)
                    continue
                if len(nodes) > 1:
                    log.error('To many nodes for service %s in the resources tree, don\'t know which one to use', typeService)
                    continue
                node = nodes[0]
                assert isinstance(node, Node)
                path = pathForNode(node)
                assert isinstance(path, Path)
                
                if __debug__:
                    # Just checking that the properties are ok
                    propertyTypes = propertyTypesOf(path, node.get)
                    assert len(propertyTypes) == 2, 'Invalid path %s for filter' % path
                    indexAuth = propertyTypes.index(resourceFilter.authenticated)
                    assert indexAuth >= 0, 'Invalid authenticated %s for path %s' % (resourceFilter.authenticated, path)
                    indexRsc = propertyTypes.index(resourceFilter.resource)
                    assert indexRsc >= 0, 'Invalid resource %s for path %s' % (resourceFilter.resource, path)
                    assert indexAuth < indexRsc, 'Invalid path %s, improper order for types' % path
                
                markerAuth = markerFor(resourceFilter.authenticated)
                replacer.register((markerAuth, '*'))
                pathMarked = '/'.join(path.toPaths(self.converterPath, replacer))
                pathAndMarkers = self._cacheFilters[typeService] = (pathMarked, {resourceFilter.authenticated: markerAuth})
                
            filtersWithPath[resourceFilter.resource] = pathAndMarkers
        return filtersWithPath

# --------------------------------------------------------------------

def markerFor(typeProperty):
    '''
    Constructs the marker for the provided property type.
    
    @param typeProperty: TypeProperty
        The property type to construct the marker for.
    @return: string
        The marker.
    '''
    assert isinstance(typeProperty, TypeProperty), 'Invalid type property %s' % typeProperty
    assert isinstance(typeProperty.container, Model)
    return '{%s.%s}' % (typeProperty.container.name, typeProperty.property)
