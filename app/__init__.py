#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it
# Copyright (C) 2026 Paolo De Stefani
# License: GPL v3

# This file is part of pysagra_web.
#
# pysagra_web is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pysagra_web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pysagra_web.  If not, see <http://www.gnu.org/licenses/>.

"""Application core module.

This module provides classes and function 
for the core functionality of the pysagra_web application.
"""

APP_NAME = 'pySagraWeb'
APP_VERSION_MAJOR = 1
APP_VERSION_MINOR = 0
APP_VERSION_PATCH = 0
FLASK_SECRET_KEY = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'


# load configuration file
import configparser
appconfig = configparser.ConfigParser()
appconfig.read('config.cfg')
