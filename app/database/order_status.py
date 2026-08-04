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

"""DatabaseOrder status

"""
# standard library
import logging

# application modules
from app.database.connect import appconn
from app.database import db_exception_context

# logger
logger = logging.getLogger(__name__)


def get_order_status(event_id: int, rows: int = 15) -> list[tuple]:
    "Return top 100 order status for monitoring"
    # actually we don't need to filter company_id as event_id and department_id are unique across companies
    script = t"""
SELECT 
    order_number						AS order_number,
	order_date	                        AS order_date,
	to_char(order_time, 'HH24:MI')		AS order_time,
	delivery							AS delivery,
	table_number						AS table_number,
	customer_name						AS customer_name,
	CASE status
		WHEN 'A' THEN 'I'
		WHEN 'P' THEN 'C'
		WHEN 'I' THEN 'L'
	END									AS status,
	to_char(fulfillment_date, 'HH24:MI') AS fulfillment,
    cast(EXTRACT(EPOCH FROM (fulfillment_date - order_date_time)) / 60 AS int) AS minutes
FROM company.vw_order_status
WHERE event_id = {event_id}
ORDER BY order_date DESC, order_time DESC
LIMIT {rows};"""
    # Unified context managers ensuring proper evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()
