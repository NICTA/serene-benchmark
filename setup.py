# Copyright 2016 Data61, CSIRO All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup script for the Serene Python client."""

from __future__ import print_function

import sys
from setuptools import setup

if sys.version_info < (3, 1):
    print('serene-benchmark requires python3 version >= 3.3.', file=sys.stderr)
    sys.exit(1)

packages = [
    'benchmark', 'karmaDSL'
]

install_requires = [
    'pandas>=0.15',
    'unittest2',
    'numpy',
    'coverage>=3.6,<4.99',
    'requests'
]

long_desc = """The Serene Benchmark is a framework to evaluate different schema matching and mapping approaches."""

import benchmark as serene_benchmark
version = serene_benchmark.__version__

setup(
    name="serene-benchmark",
    version=version,
    description="Semantic Modelling API Client Library for Python",
    long_description=long_desc,
    author="Data61 | CSIRO",
    url="http://github.com/NICTA/serene-benchmark/",
    install_requires=install_requires,
    packages=packages,
    package_data={},
    license="Apache 2.0",
    keywords="semantic modelling client serene",
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent'
    ],
)