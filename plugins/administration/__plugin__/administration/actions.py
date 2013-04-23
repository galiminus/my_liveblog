'''
Created on Feb 2, 2012

@package: introspection request
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mihai Balaceanu

Registered actions for request plugin
'''

from ..gui_action import defaults
from ..gui_action.service import addAction
from ..gui_core.gui_core import publishedURI
from ..gui_security import acl
from admin.introspection.api.component import IComponentService
from admin.introspection.api.plugin import IPluginService
from admin.introspection.api.request import IRequestService
from ally.container import ioc
from ally.internationalization import NC_
from distribution.container import app
from gui.action.api.action import Action

# --------------------------------------------------------------------

@ioc.entity
def menuAction():
    return Action('request', NC_('menu', 'Request'), Parent=defaults.menuAction(),
    NavBar='/api-requests', Script=publishedURI('superdesk/request/scripts/js/menu.js'))

@ioc.entity
def modulesAction():
    return Action('request', Parent=defaults.modulesAction())

@ioc.entity
def modulesListAction():
    return Action('list', Parent=modulesAction(), Script=publishedURI('superdesk/request/scripts/js/list.js'))

# --------------------------------------------------------------------

@ioc.entity
def rightRequestsInspection():
    return acl.actionRight(NC_('security', 'Requests inspection'), NC_('security', '''
    Allows for the viewing of all possible requests that can be made on the REST server, also the plugins and components
    that are part of the application are also visible.'''))

# --------------------------------------------------------------------

#@app.deploy
#def registerActions():
#    addAction(menuAction())
#    addAction(modulesAction())
#    addAction(modulesListAction())

#@acl.setup
#def registerAcl():
#    rightRequestsInspection().addActions(menuAction(), modulesAction(), modulesListAction())\
#    .allGet(IComponentService, IPluginService, IRequestService)
