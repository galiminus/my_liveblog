'''
Created on Nov 7, 2012

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Update the default logging.
'''

from ..ally_utilities.logging import info_for
from ally.container import ioc

# --------------------------------------------------------------------

@ioc.before(info_for)
def updateInfos():
    return info_for().append('ally.http.server')
