'''
Created on Jun 21, 2012

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Method invoker testing.
'''

# Required in order to register the package extender whenever the unit test is run.
if True:
    import package_extender
    package_extender.PACKAGE_EXTENDER.setForUnitTest(True)

# --------------------------------------------------------------------

from ally.api.config import GET
from ally.container import ioc
from ally.core.impl.node import NodeRoot
from ally.core.impl.processor.method_invoker import MethodInvokerHandler, \
    Request, Response
from ally.core.spec.resources import Path
from ally.design.processor import Chain
import unittest

# --------------------------------------------------------------------

class TestMethodInvoker(unittest.TestCase):

    def testMethodInvoker(self):
        handler = MethodInvokerHandler()
        ioc.initialize(handler)

        request, response = Request(), Response()

        node = NodeRoot()
        request.method, request.path = GET, Path([], node)

        def callProcess(chain, **keyargs): handler.process(**keyargs)
        chain = Chain([callProcess])
        chain.process(request=request, response=response).doAll()

        self.assertEqual(response.allows, 0)
        self.assertTrue(response.isSuccess is False)

# --------------------------------------------------------------------

if __name__ == '__main__': unittest.main()
