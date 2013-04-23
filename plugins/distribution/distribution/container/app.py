'''
Created on Jan 10, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the IoC container distribution support.
'''

from ._impl._app import ANALYZER, POPULATOR, DEPLOYER, SetupDistribution, \
    SetupDistributionSupport
from ally.container._impl._setup import register
from ally.container.error import SetupError
from ally.container.ioc import _process
from ally.support.util_sys import callerLocals
from functools import update_wrapper

# --------------------------------------------------------------------

def deploy(*args):
    '''
    Decorator for deploy setup functions. The deploy function will be called every time the  application is started.
    
    This should manly be used to gather data.
    '''
    return _distribution(args, DEPLOYER)

def populate(*args):
    '''
    Decorator for populate setup functions. The populate function will be called until a True or None value is returned.
    
    This should manly be used in order to populate default data. 
    If the function returns False it means it needs to be called again for the same event, if True or None is returned
    it means the function executed successfully.
    '''
    return _distribution(args, POPULATOR)

def analyze(*args):
    '''
    Decorator for analyze setup functions. The analyze function will be called every time the application distribution
    changes, basically whenever a plugin is added or updated or removed. Also the analyze will definitely be called once
    when the application is first started. 
    
    This should manly be used by plugins that need to scan the code, or is linked in any manner with the distribution
    situation.
    If the function returns False it means it needs to be called again for the same event, if True or None is returned
    it means the function executed successfully.
    '''
    return _distribution(args, ANALYZER)

# --------------------------------------------------------------------

def registerSupport():
    '''
    Register the support setup in this module in order to process the support APIs.
    '''
    register(SetupDistributionSupport(), callerLocals())

# --------------------------------------------------------------------

def _distribution(args, event):
    '''
    FOR INTERNAL USE ONLY!
    Populates the distribution setup.
    '''
    if not args: return deploy
    assert len(args) == 1, 'Expected only one argument that is the decorator function, got %s arguments' % len(args)
    function = args[0]
    hasType, type = _process(function)
    if hasType: raise SetupError('No return annotation expected for function %s' % function)
    return update_wrapper(register(SetupDistribution(function, event), callerLocals(2)), function)
