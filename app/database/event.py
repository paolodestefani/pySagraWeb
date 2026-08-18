##!/usr/bin/env python
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

"""Database - Event management

This module provides classes and functions for database management of events

"""

# standard library
from typing import Any, Tuple
import logging
from datetime import datetime

# application modules
from app.database import db_exception_context

from app.database.connect import appconn


# logger
logger = logging.getLogger(__name__)


def get_event_data(event: int) -> Tuple[Any, ...] | None:
    "Get event data"
    script = t"""
SELECT
    description,
    start_date,
    end_date,
    price_list_id
FROM event
WHERE event_id = {event};"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchone()

# def is_used(event: int) -> bool:
#     "Returns True if have orders for the given event"
#     script = t"""
# SELECT EXISTS(
#     SELECT event_id 
#     FROM order_header 
#     WHERE event_id = {event} 
#     LIMIT 1);"""
#     # Unified context managers ensuring proper evaluation order
#     with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
#         cur.execute(script)
#         result = cur.fetchone()
#         return result[0] if result else False
    
    
def get_event_from_date(date: Any) -> Any|None:
    "Get event id from date time"
    script = t"""
SELECT 
    event_id        AS event_id,
    description     AS event_description
FROM event
WHERE
        company_id = system.pa_current_company()
    AND start_date <= {date} AND end_date >= {date};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchone()
   