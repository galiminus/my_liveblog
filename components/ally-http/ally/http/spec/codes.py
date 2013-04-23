'''
Created on Jun 30, 2011

@package: ally http
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the codes to be used for the server responses.
'''

# --------------------------------------------------------------------
# Response codes.
INTERNAL_ERROR = (500, False) # HTTP code 500 Internal Server Error
INVALID_REQUEST = (400, False)  # HTTP code 400 Bad Request
INVALID_HEADER_VALUE = (400, False) # HTTP code 400 Bad Request
PATH_NOT_FOUND = (404, False)  # HTTP code 404 Not Found

