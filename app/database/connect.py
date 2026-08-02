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

"""database - connection functions

This module provide all the facilities to work with the db server
"""

# standard library
import logging
from typing import Any, Optional, ContextManager

# psycopg
import psycopg

# application modules

from app import APP_NAME
from app import APP_VERSION_MAJOR
from app import APP_VERSION_MINOR
from app import APP_VERSION_PATCH
from app import PG_MIN_VER
from app import FLASK_SECRET_KEY

# exceptions
from app.database import PyAppDBConnectionError
from app.database import PyAppDBError

# logger
logger = logging.getLogger(__name__)


# ******************************* #
#                                 #
#  connection to database server  #
#                                 #
# ******************************* #


class AppConnection():
    "Database and application connection class"

    def __init__(self) -> None:
        self._conn: psycopg.Connection # psycopg connection instance
        self._par: dict = dict() # store connection parameter

    def connect(self, par: dict) -> None:
        "Open a db connection and then an application connection trought an sql function"
        self._logging = False
        # FIRST: DATABASE CONNECTION
        logging.info("Starting database connection with parameters:")
        logging.info("host = %(server)s", par)
        logging.info("port = %(port)s", par)
        logging.info("database = %(database)s", par)
        logging.info("dbuser = %(db_user)s", par)
        logging.info("dbuser password = ********")
        logging.info("application_name = %(app_name)s", par)
        try:
            self._conn = psycopg.connect(host=par['server'],
                                         port=par['port'],
                                         dbname=par['database'],
                                         user=par['db_user'],
                                         password=par['db_password'],
                                         autocommit=True,
                                         application_name=par['app_name'])
        except psycopg.OperationalError as er:
            msg = str(er) # avoid loggin max recursion error
            logging.critical("Psycopg operational error: %s", msg) # OperationalError miss a diag attribute
            raise PyAppDBConnectionError(None, "Psycopg operational error on connection", msg)
        except psycopg.Error as er:
            logger.error("*** DATABASE ERROR ***\nSQL State: %s\n%s", er.diag.sqlstate, str(er))
            raise PyAppDBError(er.diag.sqlstate, er.diag.message_primary, str(er))
        else:
            logging.info("Database connection established")

        # OK START A NEW APPLICATION CONNECTION, if posible
        
        # check if it's an application db - if has a pa_connect function in system schema
        sql = """
SELECT EXISTS(SELECT 1 
    FROM pg_proc pr
    JOIN pg_namespace ns ON pr.pronamespace = ns.oid
    WHERE pr.proname = 'pa_connect' 
        AND ns.nspname = 'system');"""
        try:
            with self._conn.cursor() as cur:
                if self._logging:
                    logging.info(sql)
                cur.execute(sql)
                if not cur.fetchone():
                    logging.critical("Database '%s' is not an application database", par['database'])
                    raise PyAppDBError("PA0002", f"Database '{par['database']}' is not an application database")
                logging.info("DB is verified as an application database")
        except psycopg.Error as er:
            logger.error("*** DATABASE ERROR ***\nSQL State: %s\n%s", er.diag.sqlstate, str(er))
            raise PyAppDBError(er.diag.sqlstate, er.diag.message_primary, str(er))
        # connect to the applicationdb
        logging.info("Calling application connection function with parameters:")
        logging.info("pgminver = %s", PG_MIN_VER)
        logging.info("appname = %s", par['app_name'])
        logging.info("appversion = %s.%s", APP_VERSION_MAJOR, APP_VERSION_MINOR)
        logging.info("user = ********")
        logging.info("password = ********")
        logging.info("hostname = %(hostname)s", par)
        try:
            with self._conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                script = t"""
                SELECT * FROM system.pa_connect(
                    {PG_MIN_VER},
                    {par['app_name']},
                    {APP_VERSION_MAJOR},
                    {APP_VERSION_MINOR},
                    {par['user']},
                    {par['password']},
                    {par['hostname']});"""
                cur.execute(script)
                # postgres search path is set to system, common, company by pa_connect
                logging.info("DB Application connection established")
        except psycopg.Error as er:
            logger.error("*** DATABASE ERROR ***\nSQL State: %s\n%s", er.diag.sqlstate, str(er))
            raise PyAppDBError(er.diag.sqlstate, er.diag.message_primary, str(er))
        self._par.update(par)

    def change_company(self, company: int) -> None:
        "Set or change the working company"
        try:
            with self._conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(t"SELECT * FROM system.pa_company_change({company});")
        except psycopg.Error as er:
            logger.error("*** DATABASE ERROR ***\nSQL State: %s\n%s", er.diag.sqlstate, str(er))
            raise PyAppDBError(er.diag.sqlstate, er.diag.message_primary, str(er))

    def cursor(self, row_factory: Optional[psycopg.rows.RowFactory[Any]] = None,
                binary: bool = False
               ) -> psycopg.Cursor[Any]|psycopg.ServerCursor[Any]:
        "Returns a new cursor"
        if row_factory is None:
            return self._conn.cursor(binary=binary)
        else:
            return self._conn.cursor(row_factory=row_factory, binary=binary)

    def transaction(self, savepoint: str|None = None, force_rollback: bool = False
                    ) -> ContextManager[psycopg.Transaction]:
        "Returns a new transaction object"
        return self._conn.transaction(savepoint, force_rollback)

    def commit(self) -> None:
        "Commit transaction"
        self._conn.commit()

    def rollback(self) -> None:
        "Rollback transaction"
        self._conn.rollback()

    def close(self) -> None:
        "Close application and db connection"
        # log out
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT system.pa_disconnect();")
        except psycopg.Error as er:
            logger.error("*** DATABASE ERROR ***\nSQL State: %s\n%s", er.diag.sqlstate, str(er))
            raise PyAppDBConnectionError(str(er))
        # close db connection
        self._conn.close()

    def restart(self) -> None:
        self.connect(self._par)


appconn = AppConnection() # connection wrapper instance

