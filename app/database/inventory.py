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

"""Database Inventory

"""
# standard library
import logging

# application modules
from app.database.connect import appconn
from app.database import db_exception_context

# logger
logger = logging.getLogger(__name__)
       

def get_inventory(event_id: int) -> list[tuple]:
    "Inventory"
    # actually we don't need to filter company_id as event_id and department_id are unique across companies
    script = t"""
SELECT 
    it.description  AS item,
	iv.loaded       AS loaded,
	iv.unloaded     AS unloaded,
	iv.stock        AS stock,
	iv.ordered      AS ordered,
	iv.available    AS available
FROM company.inventory iv
JOIN company.item it ON iv.item_id = it.item_id
WHERE event_id = {event_id}
ORDER BY it.description;"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()
    

def get_inventory_kit_menu(event_id: int, item_type: str) -> list[tuple]:
    "Inventory"
    # actually we don't need to filter company_id as event_id and department_id are unique across companies
    script = t"""
SELECT 
    item_description,
    available
FROM company.vw_item_availability
WHERE item_type = {item_type} AND event_id = {event_id}
ORDER BY item_description;"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()

