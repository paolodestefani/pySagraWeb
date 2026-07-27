#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (C) Paolo De Stefani
# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it

"""Database - Unloads

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



def current_date():
    "Return current date considering time start/end"
    script = """
SELECT CASE WHEN current_time BETWEEN '00:00:00' AND
(SELECT (interval '1 hour' * lunch_start_time)::time FROM setting)
THEN current_date - 1
ELSE current_date END;
    """
    try:
        with appconn.cursor() as cur:
            cur.execute(script)
            return cur.fetchone()[0]
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)

def current_day_part():
    "Return current day part considering timestart/end"
    # current daty part
    script = """
SELECT CASE WHEN current_time BETWEEN
(SELECT (interval '1 hour' * lunch_start_time)::time FROM setting) AND
(SELECT (interval '1 hour' * dinner_start_time)::time FROM setting)
THEN 'L' ELSE 'D' END;
    """
    try:
        with appconn.cursor() as cur:
            cur.execute(script)
            return cur.fetchone()[0]
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)

def quantity_decimals():
    "Return quantity decimals"
    script = """
SELECT value::integer FROM system.setting WHERE setting = 'quantity_decimal_places';
    """
    try:
        with appconn.cursor() as cur:
            cur.execute(script)
            return cur.fetchone()[0]
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)

def stock_unloads(date, day_part):
    "Get a list of unloads for day/day part"
    script = """SELECT i.description,
    s.unloaded
FROM stock_unload s
JOIN item i ON s.item = i.id AND i.has_unload_control IS true
WHERE s.event_date = %s AND s.day_part = %s;"""
    try:
        with appconn.cursor() as cur:
            cur.execute(script, (date, day_part))
            return cur.fetchall()
    except psycopg2.Error as er:
        raise PyAppDBError(er.pgcode, er.pgerror)
