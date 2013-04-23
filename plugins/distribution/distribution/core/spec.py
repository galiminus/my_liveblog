'''
Created on Jan 10, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the APIs for the distribution management services.
'''

import abc

# --------------------------------------------------------------------

class IDistributionManager(metaclass=abc.ABCMeta):
    '''
    The API for the distribution manager that handles the deployment.
    '''
    
    @abc.abstractmethod
    def deploy(self, assembly=None):
        '''
        Called in order to deploy the provided assembly.
        
        @param assembly: object|None
            The assembly object to be deployed, if None the current assembly will be used.
        '''
