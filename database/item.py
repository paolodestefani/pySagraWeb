#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (C) Paolo De Stefani
# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it

"""Database - Item

"""
# standard library
import logging

# psycopg2
import psycopg2
import psycopg2.extras
import psycopg2.extensions

from database import PyAppDatabaseException
from database import PyAppDBConnectionError
from database import PyAppDBError

#from database import session

from database.connect import appconn


def item_list():
    "Get item list for supplied event and department"
    script = """SELECT item,
    item_description,
    price,
    CASE stock_control
		WHEN true AND quantity > 0 THEN true
		WHEN false THEN true
		ELSE false
	END AS available
FROM item_availability_detail
WHERE salable IS true AND web_available IS true AND event = %(event)s
ORDER BY web_sorting;"""
    try:
        with appconn.cursor() as cur:
            cur.execute(script, {'event': appconn.event})
            return cur.fetchall()
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)

def table_list():
    "Get a list of all available table code"
    script = """SELECT table_code
FROM numbered_table
WHERE is_obsolete IS false;"""
    try:
        with appconn.cursor() as cur:
            cur.execute(script)
            return [i[0] for i in cur.fetchall()]
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)