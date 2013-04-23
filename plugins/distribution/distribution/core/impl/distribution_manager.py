'''
Created on Jan 10, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the implementation for distribution management.
'''

from ally.container import wire
from ally.container._impl._assembly import Assembly
from ally.container.config import load, save, Config
from ally.container.ioc import injected
from ally.container.support import setup
from distribution.container._impl._app import DISTRIBUTION, Distribution, \
    POPULATOR, ANALYZER, DEPLOYER
from distribution.core.spec import IDistributionManager
from os.path import isfile
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

MAIN = 'main'
# Main application name
SLAVE = 'slave'
# Slave application name
DEVEL = 'devel'
# Development application name
ALL = (MAIN, SLAVE, DEVEL)
# All application names

# --------------------------------------------------------------------

@injected
@setup(IDistributionManager, name='distributionManager')
class DistributionManager(IDistributionManager):
    '''
    Implementation for @see: IDistributionManager based on a yaml configuration file.
    '''
    
    distribution_file_path = 'distribution.properties'; wire.config('distribution_file_path', doc='''
    The name of the distribution file for the plugins deployments
    ''')
    application_type = 'main'; wire.config('application_type', doc='''
    The distribution application type, the possible values are:
        main - the application behaves as the main production instance, this means:
            * the deployments are executed every time, as it should normally would
            * the analyzers are executed once on application start and every time the distribution changes,
              as it should normally would
            * the populates are executed only once as it should normally would

        slave - the application behaves as a slave production instance, this means:
            * the deployments are executed every time, as it should normally would
            * the analyzers are not executed
            * the populates are not executed
            
        devel - the application behaves as a development instance, this means:
            * the deployments are executed every time, as it should normally would
            * the analyzers are executed once on application start
            * the populates are executed only once as it should normally would
    ''')
    group_names = {
                   None: 'unused',
                   POPULATOR:'populators',
                   ANALYZER:'analyzers',
                   }
    
    def __init__(self):
        '''
        Construct the distribution manager.
        '''
        assert isinstance(self.distribution_file_path, str), 'Invalid file path %s' % self.distribution_file_path
        assert self.application_type in ALL, 'Invalid application type %s' % self.application_type
        
        self._prefix = '__plugin__.'
        self._prefixLen = len(self._prefix)
        
    def deploy(self, assembly=None):
        '''
        @see: IDistributionManager.deploy
        '''
        if assembly is None: assembly = Assembly.current()
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        distribution = assembly.calls.get(DISTRIBUTION)
        if distribution is None or distribution.assembly != assembly:
            log.info('There is no distribution in the assembly \'%s\' for deployment', assembly)
            return
        assert isinstance(distribution, Distribution), 'Invalid distribution %s' % distribution
        
        self._processDepoy(assembly, distribution)
        if self.application_type == SLAVE: return
        
        if isfile(self.distribution_file_path):
            with open(self.distribution_file_path, 'r') as f:
                data = {self._prefix + key:value for key, value in load(f).items()}
        else: data = {}
        
        if self.application_type == MAIN:
            # TODO: detect distribution changes and clear the data of those
            pass
        self._processOnce(ANALYZER, assembly, distribution, data)
        
        self._processOnce(POPULATOR, assembly, distribution, data)
        
        configs = {}
        for event in (POPULATOR, ANALYZER):
            events = distribution.events.get(event)
            if events:
                group = self.group_names[event]
                for name in events:
                    configs[name[self._prefixLen:]] = Config(name, data.pop(name, False), group)
                    
        group = self.group_names[None]
        for name, value in data.items(): configs[name[self._prefixLen:]] = Config(name, value, group)
        
        with open(self.distribution_file_path, 'w') as f: save(configs, f)

    # ----------------------------------------------------------------
    
    def _processDepoy(self, assembly, distribution):
        '''
        Process the deployments.
        '''
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        assert isinstance(distribution, Distribution), 'Invalid distribution %s' % distribution
        for name in distribution.events[DEPLOYER]: assembly.processForName(name)
        
    def _processOnce(self, event, assembly, distribution, data):
        '''
        Process the once based on the provided data.
        '''
        assert isinstance(event, int), 'Invalid event %s' % event
        assert isinstance(assembly, Assembly), 'Invalid assembly %s' % assembly
        assert isinstance(distribution, Distribution), 'Invalid distribution %s' % distribution
        assert isinstance(data, dict), 'Invalid data %s' % data
        for name in distribution.events[event]:
            if not data.get(name, False) and assembly.processForName(name):
                log.info('Deployed once the \'%s\'', name)
                data[name] = True
            
