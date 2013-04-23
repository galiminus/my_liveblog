'''
Created on Jan 10, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup implementations for the IoC distribution module.
'''

from ally.container._impl._assembly import Assembly, Setup
from ally.container._impl._call import CallEvent, WithCall, WithListeners, \
    CallEntity
from ally.container._impl._setup import SetupFunction
from ally.container.error import SetupError
from ally.support.util_sys import locationStack
from distribution.support import IDeployer, IPopulator, IAnalyzer
from functools import partial
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

DISTRIBUTION = 'distribution$repository'
# Used for identifying the distribution repository call.

DEPLOYER = 1 << 1
POPULATOR = 1 << 2
ANALYZER = 1 << 3
EVENTS = (DEPLOYER, POPULATOR, ANALYZER)
# The distribution event types

# --------------------------------------------------------------------

class SetupDistribution(SetupFunction):
    '''
    Provides the setup distribution function.
    '''

    priority_assemble = 3

    def __init__(self, function, event, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param event: integer
            On of the defined EVENTS.
        '''
        SetupFunction.__init__(self, function, **keyargs)
        assert event in EVENTS, 'Invalid event %s' % event
        self._event = event

    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name in assembly.calls:
            raise SetupError('There is already a setup call for name \'%s\', overlaps with:%s' % 
                             (self.name, locationStack(self._function)))
        if self._event == DEPLOYER:
            assembly.calls[self.name] = CallEvent(assembly, self.name, self._function)
        else:
            assembly.calls[self.name] = CallEventAcknowledged(assembly, self.name, self._function, self._event)

        _distribution(assembly).events[self._event].append(self.name)

    def __call__(self):
        '''
        Provides the actual setup of the call.
        '''
        raise SetupError('Cannot invoke the distribution setup \'%s\' directly' % self.name)
    
class SetupDistributionSupport(Setup):
    '''
    Provides the setup distribution support. This setup will deal with all the support interfaces exposed.
    '''
    
    priority_index = 1000  # Need to be the last to be indexed
    
    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        calls, dist = {}, _distribution(assembly)
        for name, call in assembly.calls.items():
            if isinstance(call, CallEntity):
                assert isinstance(call, CallEntity)
                if call.isOf(IDeployer):
                    nameEvent, event = name + '.deploy', DEPLOYER
                    caller = CallEvent(assembly, nameEvent, partial(_callDeploy, assembly, name))
                elif call.isOf(IPopulator):
                    nameEvent, event = name + '.populate', POPULATOR
                    caller = CallEventAcknowledged(assembly, nameEvent, partial(_callPopulate, assembly, name), event)
                elif call.isOf(IAnalyzer):
                    nameEvent, event = name + '.analyze', ANALYZER
                    caller = CallEventAcknowledged(assembly, nameEvent, partial(_callAnalyze, assembly, name), event)
                else: continue
                
                if nameEvent in assembly.calls:
                    raise SetupError('There is already a setup call for name \'%s\'' % nameEvent)
                calls[nameEvent] = caller
                dist.events[event].append(nameEvent)
        assembly.calls.update(calls)
        
    def __str__(self): return '<%s>' % self.__class__.__name__

# --------------------------------------------------------------------

class Distribution:
    '''
    Provides the distribution calls repository.
    @see: Callable
    '''
    
    def __init__(self, assembly):
        '''
        Construct the distribution call.
        
        @param assembly: Assembly
            The assembly to process the start calls for.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        self.assembly = assembly
        self.events = {event:[] for event in EVENTS}

    def __call__(self):
        '''
        Provides the call for the source.
        '''
        raise SetupError('Illegal call to the distribution repository')

class CallEventAcknowledged(WithCall, WithListeners):
    '''
    Provides the acknowledged event call.
    @see: Callable, WithCall, WithListeners
    '''

    def __init__(self, assembly, name, call, event):
        '''
        Construct the acknowledged event call.
        
        @param assembly: Assembly
            The assembly to which this call belongs.
        @param name: string
            The acknowledged event name.
        @param event: integer
            On of the defined EVENTS.
            
        @see: WithCall.__init__
        @see: WithListeners.__init__
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        assert isinstance(name, str), 'Invalid name %s' % name
        assert event in EVENTS, 'Invalid event %s' % event
        WithCall.__init__(self, call)
        WithListeners.__init__(self)

        self._assembly = assembly
        self.name = name
        self.event = event
        self._processed = False
        
    def addBefore(self, listener, auto):
        '''
        @see: WithListeners.addBefore
        '''
        raise SetupError('Cannot add before event to the \'%s\' distribution, only after events are allowed' % self.name)

    def validateAcceptListeners(self):
        '''
        @see: WithListeners.validateAcceptListeners
        '''
        if self._processed: raise SetupError('Already processed cannot add anymore listeners to \'%s\'' % self.name)
 
    def __call__(self):
        '''
        Provides the call for the source.
        '''
        if self._processed: return False
        self._processed = True
        self._assembly.called.add(self.name)

        try: ret = self.call()
        except:
            log.exception('A problem occurred for setup: %s' % self.name)
            ret = False
        if ret is None: ret = True
        if not isinstance(ret, bool):
            raise SetupError('The distribution call \'%s\' needs to return a boolean value' % self.name)
        if not ret: return False
        for listener, _auto in self._listenersAfter: listener()
        return True

# --------------------------------------------------------------------

def _distribution(assembly):
    dist = assembly.calls.get(DISTRIBUTION)
    if dist is None or dist.assembly != assembly: dist = assembly.calls[DISTRIBUTION] = Distribution(assembly)
    # We need also to check if the deploy call is not inherited from a parent assembly.
    return dist

def _callDeploy(assembly, name):
    '''
    Used to call the deploy.
    '''
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    assert isinstance(name, str), 'Invalid name %s' % name
    entity = assembly.processForName(name)
    assert isinstance(entity, IDeployer), 'Invalid deployer %s' % entity
    entity.doDeploy()
    
def _callPopulate(assembly, name):
    '''
    Used to call the populate.
    '''
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    assert isinstance(name, str), 'Invalid name %s' % name
    entity = assembly.processForName(name)
    assert isinstance(entity, IPopulator), 'Invalid populator %s' % entity
    return entity.doPopulate()

def _callAnalyze(assembly, name):
    '''
    Used to call the analyzer.
    '''
    assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
    assert isinstance(name, str), 'Invalid name %s' % name
    entity = assembly.processForName(name)
    assert isinstance(entity, IAnalyzer), 'Invalid analyzer %s' % entity
    return entity.doAnalyze()
