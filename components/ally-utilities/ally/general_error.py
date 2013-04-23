'''
Created on May 31, 2011

@package: ally utilities
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides general errors.
'''

# --------------------------------------------------------------------

class DevelopmentError(Exception):
    '''
    Wraps exceptions that are related to wrong development usage.
    '''

    def __init__(self, message):
        assert isinstance(message, str), 'Invalid string message %s' % message
        self.message = message
        Exception.__init__(self, message)
