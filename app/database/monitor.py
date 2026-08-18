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

"""Database Monitor

"""
# standard library
import logging

# application modules
from app.database.connect import appconn
from app.database import db_exception_context

# logger
logger = logging.getLogger(__name__)
       
    
    
def get_inventory(event_id) -> list[tuple]:
    script = t"""
-- normal items type = 0 header = 9
SELECT 9 AS type, 'NORMAL ITEMS' AS item, Null AS loaded, Null AS unloaded, Null AS stock, Null AS ordered, Null AS available
UNION ALL
SELECT 
	0				            AS type,
    it.description              AS item,
	cast(iv.loaded      as int) AS loaded,
	cast(iv.unloaded    as int) AS unloaded,
	cast(iv.stock       as int) AS stock,
	cast(iv.ordered     as int) AS ordered,
	cast(iv.available   as int) AS available
FROM company.inventory iv
JOIN company.item it ON iv.item_id = it.item_id
WHERE event_id = {event_id}
UNION ALL
-- kit items type = 1 header = 9
SELECT 
    9                           AS type, 
    'KIT ITEMS'                 AS item, 
    Null                        AS loaded, 
    Null                        AS unloaded, 
    Null                        AS stock, 
    Null                        AS ordered, 
    Null                        AS available
UNION ALL
SELECT 
	1					        AS type,
    item_description	        AS item,
	Null       			        AS loaded,
	Null     			        AS unloaded,
	Null        		        AS stock,
	Null      			        AS ordered,
	cast(available as int)		AS available
FROM company.vw_item_availability
WHERE item_type = 'K' AND event_id = {event_id}
UNION ALL
-- menu items type = 2 header = 9
SELECT 
    9                           AS type,
    'MENU ITEMS'                AS item,
    Null                        AS loaded,
    Null                        AS unloaded,
    Null                        AS stock,
    Null                        AS ordered,
    Null                        AS available
UNION ALL
SELECT 
	2					        AS type,
    item_description	        AS item,
	Null       			        AS loaded,
	Null     			        AS unloaded,
	Null        		        AS stock,
	Null      			        AS ordered,
	cast(available as int) 		AS available
FROM company.vw_item_availability
WHERE item_type = 'M' AND event_id = {event_id};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()
    
    
def get_ordered_delivered(event_id) -> list[tuple]:
    script = t"""
SELECT 
    s.event_id                  AS event,
    s.event_date                AS date,
    s.day_part                  AS day_part,
    s.item_id                   AS item_id,
    i.description               AS item,
    cast(s.ordered      as int) AS ordered,
    cast(s.delivered    as int) AS delivered
FROM ordered_delivered s
JOIN item i ON s.item_id = i.item_id
WHERE s.event_id = {event_id};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()
    
def get_sales_summary(event_id) -> list[tuple]:
    script = t"""
SELECT 
    -- event_id                             AS event,
    -- event_description                    AS event_Description,
    order_date                              AS order_date,
    -- num_orders_lunch                        AS num_orders_lunch,
    -- num_orders_dinner                       AS num_orders_dinner,
    num_orders_lunch + num_orders_dinner    AS num_orders,
    -- num_covers_lunch                        AS num_covers_lunch,
    -- num_covers_dinner                       AS num_covers_dinner,
    num_covers_lunch + num_covers_dinner    AS num_covers,
    -- take_away_lunch                         AS take_away_lunch,
    -- take_away_dinner                        AS take_away_dinner,
    take_away_lunch + take_away_dinner      AS take_away,
    -- table_lunch                             AS table_lunch,
    -- table_dinner                            AS table_dinner,
    table_lunch + table_dinner              AS table,
    -- amount_lunch                            AS amount_lunch,
    -- amount_dinner                           AS amount_dinner,  
    amount_lunch + amount_dinner            AS amount,
    -- discount_lunch                          AS discount_lunch,
    -- discount_dinner                         AS discount_dinner,
    discount_lunch + discount_dinner        AS discount,
    -- electronic_lunch                        AS electronic_lunch,
    -- electronic_dinner                       AS electronic_dinner,
    electronic_lunch + electronic_dinner    AS electronic,
    -- cash_lunch                              AS cash_lunch,
    -- cash_dinner                             AS cash_dinner,
    cash_lunch + cash_dinner                AS cash,
    -- total_lunch                             AS total_lunch,
    -- total_dinner                            AS total_dinner,
    total_lunch + total_dinner              AS total
FROM vw_sales_summary
WHERE event_id = {event_id};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()


    

