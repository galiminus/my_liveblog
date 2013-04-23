'''
Created on Jan 9, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Support APIs that allow the distribution management. The order of the APIs execution is:

@see: IDeployer
@see: IPopulator
@see: IAnalyzer
'''

import abc

# --------------------------------------------------------------------

class IDeployer(metaclass=abc.ABCMeta):
    '''
    If an entity is tagged with this interface and appears in the IoC context it will automatically call the process
    deploy method at the end of the distribution process. The process deploy method will be called every time the 
    application is started.
    
    This should manly be used to gather data.
    '''
    
    @abc.abstractmethod
    def doDeploy(self):
        '''
        Method called once for application start if the implementation appears in the IoC assembly.
        '''
        
class IAnalyzer(metaclass=abc.ABCMeta):
    '''
    If an entity is tagged with this interface and appears in the IoC context it will automatically call the process
    analyze method at the end of the distribution process. The process analyze method will be called every time the
    application distribution changes, basically whenever a plugin is added or updated or removed. Also the analyze
    will definitely be called once when the application is first started. 
    
    This should manly be used by plugins that need to scan the code, or is linked in any manner with the distribution
    situation.
    '''
    
    @abc.abstractmethod
    def doAnalyze(self):
        '''
        Method called when the application is first started or the distribution changes, the method will be called until
        it returns a True value thus acknowledging the event, if False is returned the method will be called until it
        returns a True value. Available only if the implementation appears in the IoC assembly.
        
        @return: boolean|None
            If True or None is returned then this method will acknowledge the event and not be called again for the same
            event.
        '''
        
class IPopulator(metaclass=abc.ABCMeta):
    '''
    If an entity is tagged with this interface and appears in the IoC context it will automatically call the process
    populate method at the end of the distribution process. The process populate method will be called until a True
    value is returned.
    
    This should manly be used in order to populate default data. 
    '''
    
    @abc.abstractmethod
    def doPopulate(self):
        '''
        Method called until it returns a True value, available only if the implementation appears in the IoC assembly.
        
        @return: boolean|None
            If True or None is returned then this method will not be called again.
        '''
