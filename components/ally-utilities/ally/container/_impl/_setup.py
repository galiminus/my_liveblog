'''
Created on Jan 12, 2012

@package: ally utilities
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup implementations for the IoC module.
'''

from ..config import Config
from ..error import SetupError, ConfigError
from ._assembly import Setup, Assembly
from ._call import WithType, WithCall, CallEvent, CallEventOnCount, \
    WithListeners, CallConfig, CallEntity, CallStart
from ally.support.util_sys import locationStack
from functools import partial
from inspect import isclass, isfunction, getfullargspec, getdoc
from numbers import Number
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

START_CALL = 'start$call'
# Used for identifying the start call.

# --------------------------------------------------------------------

def setupFirstOf(register, *classes):
    '''
    Provides the first setup in the register that is of the provided class.
    
    @param register: dictionary{string, object}
        The register to retrieve the setup from.
    @param classes: arguments[class]
        The setup class(es) to find for.
    @return: Setup|None
        The first found setup or None.
    '''
    assert isinstance(register, dict), 'Invalid register %s' % register
    setups = register.get('__ally_setups__')
    if setups is not None:
        for setup in setups:
            if isinstance(setup, classes): return setup
    return None

def setupsOf(register, *classes):
    '''
    Provides the setups in the register that are of the provided class.
    
    @param register: dictionary{string, object}
        The register to retrieve the setups from.
    @param classes: arguments[class]
        The setup class(es) to find for.
    @return: list[Setup]
        The setups list.
    '''
    assert isinstance(register, dict), 'Invalid register %s' % register
    setups = register.get('__ally_setups__')
    if setups is not None:
        return [setup for setup in setups if isinstance(setup, classes)]
    return []

def register(setup, register):
    '''
    Register the setup function into the calling module.
    
    @param setup: Setup
        The setup to register into the calling module.
    @param register: dictionary{string, object}
        The register to place the setup in.
    @return: Setup
        The provided setup entity.
    '''
    assert isinstance(register, dict), 'Invalid register %s' % register
    setups = register.get('__ally_setups__')
    if setups is None: setups = register['__ally_setups__'] = []
    setups.append(setup)
    return setup

# --------------------------------------------------------------------

class SetupFunction(Setup):
    '''
    A setup indexer based on a function.
    '''

    def __init__(self, function, name=None, group=None):
        '''
        Constructs the setup call for the provided function.
        
        @param function: function|Callable
            The function of the setup call, lambda functions or Callable are allowed only if the name is provided.
        @param name: string|None
            The name of this setup, if not specified it will be extracted from the provided function.
        @param group: string|None
            The group of this setup, if not specified it will be extracted from the provided function.
        '''
        assert not group or isinstance(group, str), 'Invalid group %s' % group
        if name:
            assert callable(function), 'Invalid callable function %s' % function
            assert isinstance(name, str), 'Invalid name %s' % name
            self.name = name
            self.group = group
        else:
            assert isfunction(function), 'Invalid function %s' % function
            assert function.__name__ != '<lambda>', 'Lambda functions cannot be used %s' % function
            if group: self.group = group
            else: self.group = function.__module__
            self.name = self.group + '.' + function.__name__
            if __debug__:
                fnArgs = getfullargspec(function)
                assert not (fnArgs.args or fnArgs.varargs or fnArgs.varkw), \
                'The setup function \'%s\' cannot have any type of arguments' % self.name
        self._function = function

    def __call__(self):
        '''
        Provides the actual setup of the call.
        '''
        return Assembly.process(self.name)
    
    def __str__(self): return '%s at:%s' % (self.__class__.__name__, locationStack(self._function))

class SetupSource(SetupFunction, WithType):
    '''
    Provides the setup for retrieving a value based on a setup function.
    '''

    def __init__(self, function, types=None, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param types: Iterable(class)|None
            The type(class) of the value that is being delivered by this source.
        '''
        SetupFunction.__init__(self, function, **keyargs)
        WithType.__init__(self, types)

class SetupSourceReplace(SetupFunction, WithType):
    '''
    Provides the setup for replacing source setup function.
    '''

    def __init__(self, function, target, types=None, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param target: SetupSource
            The setup to be replaced.
        '''
        assert isinstance(target, SetupSource), 'Invalid target %s' % target
        SetupFunction.__init__(self, function, name=target.name, group=target.group, ** keyargs)
        WithType.__init__(self, types)
        self.priority_assemble = target.priority_assemble + 1

    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name not in assembly.calls:
            raise SetupError('There is no setup call for name \'%s\' to be replaced by:%s' % 
                             (self.name, locationStack(self._function)))
        call = assembly.calls[self.name]
        if not isinstance(call, WithCall) and not isinstance(call, WithType):
            raise SetupError('Cannot replace call for name \'%s\' from:%s' % (self.name, locationStack(self._function)))
        assert isinstance(call, WithCall)
        call.call = self._function
        if self._types:
            assert isinstance(call, WithType)
            if call.types:
                found = False
                for clazz in self._types:
                    for clazzCall in call.types:
                        if clazz == clazzCall or issubclass(clazz, clazzCall):
                            found = True
                            break
                    if found: break
                if not found: raise SetupError('There is no common class for replaced classes %s and replace classes %s' % 
                                               ([str(clazz) for clazz in self._types], [str(clazz) for clazz in call.types]))
            
            call.types = self._types

class SetupEntity(SetupSource):
    '''
    Provides the entity setup.
    '''

    def __init__(self, function, **keyargs):
        '''
        @see: SetupSource.__init__
        '''
        SetupSource.__init__(self, function, **keyargs)

    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name in assembly.calls:
            raise SetupError('There is already a setup call for name %r' % self.name)
        assembly.calls[self.name] = CallEntity(assembly, self.name, self._function, self._types)

class SetupConfig(SetupSource):
    '''
    Provides the configuration setup.
    '''

    priority_assemble = 3

    def __init__(self, function, **keyargs):
        '''
        @see: SetupSource.__init__
        '''
        SetupSource.__init__(self, function, **keyargs)
        self._types = tuple(normalizeConfigType(clazz) for clazz in self._types)
        self.documentation = getdoc(function)

    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name in assembly.calls:
            raise SetupError('There is already a setup call for name %r' % self.name)

        assembly.calls[self.name] = CallConfig(assembly, self.name, self._types)

    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        Checks for aliases to replace.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        config = assembly.calls.get(self.name)
        assert isinstance(config, CallConfig), 'Invalid call configuration %s' % config

        for name, val in assembly.configExtern.items():
            if name == self.name or self.name.endswith('.' + name):
                if name in assembly.configUsed:
                    raise SetupError('The configuration %r is already in use and the configuration "%s" cannot use it '
                                     'again, provide a more detailed path for the configuration (ex: "ally_core.url" '
                                     'instead of "url")' % (name, self.name))
                assembly.configUsed.add(name)
                config.external, config.value = True, val

        if not config.hasValue:
            try: config.value = self._function()
            except ConfigError as e: config.value = e

        cfg = assembly.configurations.get(self.name)
        if not cfg:
            cfg = Config(self.name, config.value, self.group, self.documentation)
            assembly.configurations[self.name] = cfg
        else:
            assert isinstance(cfg, Config), 'Invalid configuration %s' % cfg
            cfg.value = config.value

class SetupConfigReplace(SetupFunction):
    '''
    Provides the setup for replacing a configuration setup function.
    '''

    def __init__(self, function, target, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param target: SetupFunction
            The setup name to be replaced.
        '''
        assert isinstance(target, SetupConfig), 'Invalid target %s' % target
        SetupFunction.__init__(self, function, name=target.name, group=target.group, ** keyargs)
        documentation = getdoc(function)
        if documentation:
            if target.documentation: target.documentation += '\n%s' % documentation
            else: target.documentation = documentation
        self.target = target
        self.priority_assemble = target.priority_assemble - 1

    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name not in assembly.calls:
            raise SetupError('There is no setup configuration call for name \'%s\' to be replaced by:%s' % 
                             (self.name, locationStack(self._function)))
        config = assembly.calls[self.name]
        assert isinstance(config, CallConfig), 'Invalid call configuration %s' % config
        try: config.value = self._function()
        except ConfigError as e: config.value = e

        assembly.configurations[self.name] = Config(self.name, config.value, self.group, self.target.documentation)

class SetupEvent(SetupFunction):
    '''
    Provides the setup event function.
    '''

    priority_assemble = 4

    BEFORE = 1 << 1
    AFTER = 1 << 2
    EVENTS = (BEFORE, AFTER)

    def __init__(self, function, target, event, auto, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param target: string|tuple(string)
            The target name of the event call.
        @param event: integer
            On of the defined EVENTS.
        @param auto: boolean
            Flag indicating that the event call should be auto managed by the container.
        '''
        SetupFunction.__init__(self, function, **keyargs)
        if isinstance(target, str): targets = (target,)
        else: targets = target
        assert isinstance(targets, tuple), 'Invalid targets %s' % targets
        if __debug__:
            for target in targets: assert isinstance(target, str), 'Invalid target %s' % target
        assert event in self.EVENTS, 'Invalid event %s' % event
        assert isinstance(auto, bool), 'Invalid auto flag %s' % auto
        self._targets = targets
        self._event = event
        self._auto = auto

    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name in assembly.calls:
            raise SetupError('There is already a setup call for name \'%s\', overlaps with:%s' % 
                             (self.name, locationStack(self._function)))
        if self._event == self.BEFORE or len(self._targets) == 1:
            assembly.calls[self.name] = CallEvent(assembly, self.name, self._function)
        else:
            assembly.calls[self.name] = CallEventOnCount(assembly, self.name, self._function, len(self._targets))

    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        for target in self._targets:
            if target not in assembly.calls:
                raise SetupError('There is no setup call for target \'%s\' to add the event on:%s' % 
                                 (target, locationStack(self._function)))
            call = assembly.calls[target]
            if not isinstance(call, WithListeners):
                raise SetupError('Cannot find any listener support for target \'%s\' to add the event on:%s' % 
                                 (target, locationStack(self._function)))
            assert isinstance(call, WithListeners)
            try:
                if self._event == self.BEFORE: call.addBefore(partial(assembly.processForName, self.name), self._auto)
                elif self._event == self.AFTER: call.addAfter(partial(assembly.processForName, self.name), self._auto)
            except SetupError:
                raise SetupError('Cannot add listener for \'%s\' from:%s' % (self._event, locationStack(self._function)))

    def __call__(self):
        '''
        Provides the actual setup of the call.
        '''
        raise SetupError('Cannot invoke the event setup \'%s\' directly' % self.name)

class SetupEventReplace(SetupFunction):
    '''
    Provides the setup for replacing event setup function.
    '''

    def __init__(self, function, target, types=None, **keyargs):
        '''
        @see: SetupFunction.__init__
        
        @param target: SetupEvent
            The setup to be replaced.
        '''
        assert isinstance(target, SetupEvent), 'Invalid target %s' % target
        SetupFunction.__init__(self, function, name=target.name, group=target.group, **keyargs)
        self.priority_assemble = target.priority_assemble + 1

    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name not in assembly.calls:
            raise SetupError('There is no setup call for name \'%s\' to be replaced by:%s' % 
                             (self.name, locationStack(self._function)))
        call = assembly.calls[self.name]
        if not isinstance(call, WithCall) and not isinstance(call, WithType):
            raise SetupError('Cannot replace call for name \'%s\' from:%s' % (self.name, locationStack(self._function)))
        assert isinstance(call, WithCall)
        call.call = self._function

class SetupStart(SetupFunction):
    '''
    Provides the start function.
    '''

    def __init__(self, function, priority=0, **keyargs):
        '''
        @see: SetupFunction.__init__
        '''
        assert isinstance(priority, int), 'Invalid priority %s' % priority
        SetupFunction.__init__(self, function, **keyargs)
        self.priority_assemble += priority

    def index(self, assembly):
        '''
        @see: Setup.index
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        if self.name in assembly.calls:
            raise SetupError('There is already a setup call for name \'%s\', overlaps with:%s' % 
                             (self.name, locationStack(self._function)))
        assembly.calls[self.name] = CallEvent(assembly, self.name, self._function)
        
    def assemble(self, assembly):
        '''
        @see: Setup.assemble
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        start = assembly.calls.get(START_CALL)
        if start is None or start.assembly != assembly: start = assembly.calls[START_CALL] = CallStart(assembly)
        # We need also to check if the start call is not inherited from a parent assembly.
        
        start.names.appendleft(self.name)

# --------------------------------------------------------------------

def normalizeConfigType(clazz):
    '''
    Checks and normalizes the provided configuration type.
    
    @param clazz: class
        The configuration type to normalize.
    @return: class
        The normalized type.
    '''
    if clazz:
        assert isclass(clazz), 'Invalid class %s' % clazz
        if clazz == float: return Number
    return clazz
