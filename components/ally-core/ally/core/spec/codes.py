'''
Created on Jun 30, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the codes to be used for the server responses.
'''

# --------------------------------------------------------------------
# Response codes.
UNKNOWN_ENCODING = (400, False)  # HTTP code 400 Bad Request
BAD_CONTENT = (400, False)  # HTTP code 400 Bad Request
ILLEGAL_PARAM = (400, False)  # HTTP code 400 Bad Request
RESOURCE_NOT_FOUND = (404, False)  # HTTP code 404 Not Found
METHOD_NOT_AVAILABLE = (501, False)  # HTTP code 501 Unsupported method
INCOMPLETE_ARGUMENTS = (400, False)  # HTTP code 400 Bad Request
INPUT_ERROR = (400, False)  # HTTP code 400 Bad Request
CANNOT_DELETE = (404, False)  # HTTP code 404 Not Found
CANNOT_UPDATE = (404, False)  # HTTP code 404 Not Found
CANNOT_INSERT = (404, False)  # HTTP code 404 Not Found

RESOURCE_FOUND = (200, True)  # HTTP code 200 OK
REDIRECT = (302, True)  # HTTP code 302 originally temporary redirect, but now commonly used to specify redirection
# for unspecified reason
DELETED_SUCCESS = (204, True)  # HTTP code 204 No Content
UPDATE_SUCCESS = (200, True)  # HTTP code 200 OK
INSERT_SUCCESS = (201, True)  # HTTP code 201 Created
