#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ 
    "pyodbc",
    "peewee>=3.12.0",
    "loguru"
 ]

test_requirements = ['pytest>=3', ]

setup(
    author="uncle didi",
    author_email='egde@pm.me',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Extending peewee to use MS SQL Server and Azure SQL Server",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='didis_peewee_mssql',
    name='didis_peewee_mssql',
    packages=find_packages(include=['didis_peewee_mssql', 'didis_peewee_mssql.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/egde/didis_peewee_mssql',
    version='0.1.0',
    zip_safe=False,
)
