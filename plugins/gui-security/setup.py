'''
Created on June 14, 2012

@package: GUI acl
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mugur Rus
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name="gui_security",
    version="1.0",
    packages=find_packages(),
    install_requires=['gui_action >= 1.0', 'security >= 1.0'],
    platforms=['all'],
    zip_safe=True,

    # metadata for upload to PyPI
    author="Gabriel Nistor",
    author_email="gabriel.nistor@sourcefabric.org",
    description="Ally framework - GUI actions plugin",
    long_description='The plugin that provides the support for configuring access for the gui actions',
    license="GPL v3",
    keywords="Ally REST framework plugin acl GUI",
    url="http://www.sourcefabric.org/en/superdesk/", # project home page
)
