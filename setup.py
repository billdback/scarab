"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from setuptools import setup, find_packages

setup(name='scarab',
      version='1.0',
      description='This package contains the framework for an entity-based event simulation framework.',
      python_requires='>3.6',
      author='William D Back',
      author_email='billback@mac.com',
      license='GPL3',
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
            "pyyaml"
      ]
      )
