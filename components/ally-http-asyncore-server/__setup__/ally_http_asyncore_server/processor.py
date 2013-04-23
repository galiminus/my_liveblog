'''
Created on Nov 24, 2011

@package: ally http
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the setup for the asyncore processor.
'''

from ally.container import ioc
from os import path

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def dump_requests_size():
    '''The minimum size of the request length to be dumped on the file system in bytes'''
    return 1024 * 1024

@ioc.config
def dump_requests_path():
    '''The path where the requests are dumped when they are to big to keep in memory'''
    return path.join('workspace', 'asyncore')

