'''
Created on Jun 1, 2012

@package: ally core http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides HTTP server specification.
'''

from ally.api.config import GET, DELETE, INSERT, UPDATE
from ally.http.spec.server import METHOD_GET, METHOD_DELETE, METHOD_POST, \
    METHOD_PUT, METHOD_OPTIONS
from ally.support.util import immut
import abc

# --------------------------------------------------------------------
# Additional HTTP methods.

OPTIONS = 16
UNKNOWN = -1

METHODS_TO_CORE = immut({METHOD_GET: GET, METHOD_DELETE: DELETE, METHOD_POST: INSERT,
                         METHOD_PUT: UPDATE, METHOD_OPTIONS: OPTIONS})

CORE_TO_METHODS = immut({GET: METHOD_GET, DELETE: METHOD_DELETE, INSERT: METHOD_POST,
                         UPDATE: METHOD_PUT, OPTIONS: METHOD_OPTIONS})

# --------------------------------------------------------------------

class IEncoderPath(metaclass=abc.ABCMeta):
    '''
    Provides the path encoding.
    '''

    @abc.abstractmethod
    def encode(self, path, parameters=None):
        '''
        Encodes the provided path to a full request path.
        
        @param path: Path|string
            The path to be encoded, for a local REST resource it will be a Path object, also it can be a string that will
            be interpreted as a path.
        @param parameters: list
            A list of tuples containing on the first position the parameter string name and on the second the string
            parameter value as to be represented in the request path.
        @return: object
            The full compiled request path, the type depends on the implementation.
        '''
