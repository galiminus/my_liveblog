'''
Created on Jan 10, 2013

@package: distribution manager
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the deploy setup for distribution management.
'''

from distribution.container import app
from distribution.core.spec import IDistributionManager
from ally.container import ioc, support

# --------------------------------------------------------------------

support.createEntitySetup('distribution.**.impl.**.*')
app.registerSupport()

# --------------------------------------------------------------------

@ioc.start(priority= -1)  # The lowest priority
def deploy(): support.entityFor(IDistributionManager).deploy()
