'''
Created on June 14, 2012

@package: security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Ioan v. Pocol
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name="security_http_acl",
    version="1.0",
    packages=find_packages(),
    install_requires=['security >= 1.0'],
    platforms=['all'],
    zip_safe=True,

    # metadata for upload to PyPI
    author="Gabriel Nistor",
    author_email="gabriel.nistor@sourcefabric.org",
    description="Security for HTTP gateway",
    long_description='Access control layer for HTTP gateway',
    license="GPL v3",
    keywords="Ally REST framework security plugin acl",
    url="http://www.sourcefabric.org/en/superdesk/",  # project home page
)
