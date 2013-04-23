'''
Created on Nov 23, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Runs the basic web server.
'''

from . import server_type, server_version, server_host, server_port
from ally.container import ioc
from ally.http.server import server_basic
from ally.http.server.wsgi import RequestHandler
from threading import Thread

# --------------------------------------------------------------------

@ioc.entity
def pathAssemblies():
    '''
    The path assemblies to be processed, add to this list tuples containing in the first position the pattern to be matched
    with the request path and on the second position the Assembly object to be used for requests that match the pattern.
    '''
    return []

@ioc.entity
def requestHandlerWSGI():
    b = RequestHandler(); yield b
    b.pathAssemblies = pathAssemblies()
    b.serverVersion = server_version()

# --------------------------------------------------------------------

@ioc.start
def runServer():
    if server_type() == 'basic':
        args = pathAssemblies(), server_version(), server_host(), server_port()
        Thread(name='HTTP server thread', target=server_basic.run, args=args).start()
