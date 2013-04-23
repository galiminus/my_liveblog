'''
Created on June 14, 2012

@package: service security
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor
'''

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup(
    name='service_security',
    version='1.0',
    packages=find_packages(),
    install_requires=['ally_http >= 1.0'],
    platforms=['all'],
    test_suite='test',
    zip_safe=True,
    package_data={
        '': ['*.zip'],
    },

    # metadata for upload to PyPI
    author='Gabriel Nistor',
    author_email='mugur.rus@sourcefabric.org, gabriel.nistor@sourcefabric.org',
    description='Ally framework - Security gateway service',
    long_description='The security service of the Ally framework',
    license='GPL v3',
    keywords='Ally HTTP framework',
    url='http://www.sourcefabric.org/en/superdesk/',  # project home page
)
