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

"""Database - Seat map management

This module provides classes and functions for database seat map management

"""

# standard library
import logging

# application modules
from app.database.connect import appconn
from app.database import db_exception_context


# logger
logger = logging.getLogger(__name__)


def table_list() -> list[tuple[str, int, int, str, str, bool]]:
    "Returns a list of available table codes"
    script = t"""
SELECT 
    table_code,
    pos_row,
    pos_column,
    text_color,
    background_color,
    is_unavailable
FROM company.seat_map
WHERE 
        company_id = system.pa_current_company() 
    AND is_obsolete IS false;
"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()

