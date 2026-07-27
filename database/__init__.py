#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it
# Copyright (C) Paolo De Stefani
# License: GPL v3



# exceptions

# Exceptions hierarchy
#
# PyAppDatabaseException
#   -> PyAppDBError
#      -> PyAppDBConnectionError
#      -> PyAppDBFunctionError



class PyAppDatabaseException(Exception):
    "Base exception class"
    pass


class PyAppDBConnectionError(PyAppDatabaseException):
    "Errors on connectiong to database server"
    pass


class PyAppDBError(PyAppDatabaseException):
    "Error on interacting with database server"

    def __init__(self, code=None, message=None):
        super().__init__(code, message)
        self.code = code
        self.message = message


APPNAME = 'pySagra'
APPVERSIONMAJOR = 1
APPVERSIONMINOR = 0
PGMINVER = 10


