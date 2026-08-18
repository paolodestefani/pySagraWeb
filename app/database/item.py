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

"""Database - Item

"""
# standard library
import logging

# application modules
from app.database.connect import appconn
from app.database import db_exception_context

# logger
logger = logging.getLogger(__name__)


def get_variants(item_id: int | None) -> list[tuple]:
    "Get a list of variants from item_id"
    # actually we don't need to filter company_id as item_id is unique across companies
    script = t"""
SELECT 
    variant_description AS description,
    price_delta         AS delta
FROM item_variant
WHERE   company_id  = system.pa_current_company() 
    AND item_id     = {item_id}
ORDER BY sorting;"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()


def item_list(event_id: int, department_id: int) -> list[tuple]:
    "Get item list for supplied event and department"
    # actually we don't need to filter company_id as event_id and department_id are unique across companies
    script = t"""
SELECT 
    is_salable,
    item_type,
    item_id,
    item_description,
    price,
    pos_row,
    pos_column,
    has_inventory_control,
    has_delivered_control,
    normal_text_color,
    normal_background_color,
    has_variants,
    available
FROM vw_item_availability
WHERE 
        company_id      = system.pa_current_company() 
    AND event_id        = {event_id} 
    AND department_id   = {department_id};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()
        
    
def item_web_list(event_id: int, department_id: int) -> list[tuple]:
    "Get item list for supplied event for web order"
    # actually we don't need to filter company_id as event_id and department_id are unique across companies
    script = t"""
SELECT 
    item_id                     AS id,
    item_customer_description   AS description,
    price                       AS price,
    is_available                AS available,
    has_variants                AS variants
FROM vw_item_availability
WHERE 
        company_id      = system.pa_current_company() 
    AND is_salable      IS true 
    AND is_web_available IS true 
    AND event_id        = {event_id} 
    AND department_id   = {department_id}
ORDER BY web_sorting;"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()