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

"""Database - Department

Function for databse management of departments

"""

# standard library
import logging

# psycopg
#import psycopg

# application modules
from app.database.connect import appconn
from app.database import db_exception_context


# logger
logger = logging.getLogger(__name__)



def department_list(only_active: bool = True,
                    include_menu: bool = False
                    ) -> list[tuple]:
    "Get a list of active departments or all departments"
    where = []
    where.append('company_id = system.pa_current_company()')
    if only_active is True:
        where.append('is_obsolete IS false')
    if include_menu is False:
        where.append('is_menu_container IS false')
    if where:
        script = (f"""
SELECT department_id, description
FROM department """
f"""WHERE {' AND '.join(where)} """
f"""ORDER BY sorting;""")
    else:
        script = """
SELECT department_id, description
FROM department
WHERE company_id = system.pa_current_company()
ORDER BY sorting;"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()


def department_web_list() -> list[tuple]:
    "Get a list of active departments with has items web available"
    script = """
SELECT
	d.department_id,
	d.description
FROM company.department d
JOIN (
	-- department that have items web available and not obsolete
	SELECT DISTINCT
		d.department_id
	FROM company.department d
	JOIN company.item i ON d.department_id = i.department_id
	WHERE i.is_obsolete is false AND i.is_web_available is true
	) da ON d.department_id = da.department_id
WHERE
        company_id = system.pa_current_company()
    AND d.is_obsolete IS false
ORDER BY d.sorting;"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return cur.fetchall()


def get_department(desc: str) -> int | None:
    "Returns department id of given department description"
    script = t"""
SELECT department_id 
FROM department 
WHERE 
        company_id = system.pa_current_company()
    AND description = {desc};"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        result = cur.execute(script).fetchone()
        if result:
            return result[0]
        return None


def get_department_desc(dep: int) -> str | None:
    "Returns department description of given department id"
    script = t"""
SELECT description 
FROM department 
WHERE department_id = {dep};"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        result = cur.execute(script).fetchone()
        if result:
            return result[0]
        return None

    
def get_department_barcode(dep: int) -> str | None:
    "Returns department barcode of given department id"
    script = t"""
SELECT chr(cast(count(*) + 64 as integer)) AS n 
FROM company.department 
WHERE   
        department_id <= {dep}
    AND company_id = system.pa_current_company();"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        result = cur.execute(script).fetchone()
        if result:
            return result[0]
        return None


def get_department_printer_class(dep: int) -> int | None:
    "Returns the printer class for dep department"
    script = t"""
SELECT printer_class_id
FROM department
WHERE 
        department_id = {dep} 
    AND is_obsolete IS false 
    AND is_menu_container IS false;"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        result = cur.execute(script).fetchone()
        if result:
            return result[0]
        return None
    

def department_takeaway_list()-> list[str]:
    "Returns a list of departments enabled for take away"
    script = """
SELECT description 
FROM department 
WHERE
    company_id = system.pa_current_company()
    AND is_for_takeaway IS True;"""
    # Unified context managers in the recommended evaluation order
    with db_exception_context(logger), appconn.transaction(), appconn.cursor() as cur:
        cur.execute(script)
        return [i[0] for i in cur.fetchall()]
    