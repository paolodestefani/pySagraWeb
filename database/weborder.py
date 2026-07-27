#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (C) Paolo De Stefani
# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it

"""Database - Order management

"""
# psycopg2
import psycopg2
import psycopg2.extras
import psycopg2.extensions

from database import PyAppDatabaseException
from database import PyAppDBConnectionError
from database import PyAppDBError

#from database import session

from database.connect import appconn


class Record(dict):
    """The Record class is a dictionary subclass and stores a record of a 
    database table. The constructor keep a reference of the table name and 
    primary key fields. The dictionary keys are fields name of the database 
    table.
    4 additional methods are metodi are added to the dictionary class:
        - select_record for select one record from the database table based on a primary key
        - insert_record for inserting the record in the table
        - update_record for update the record in the table based on the primary key
        - delete_record for delete the record in the table based on the primary key
    """

    def __init__(self, table, pkey = []):
        """- table = table name
           - pkey = list of primary key's fields for update/delete"""
        self.table = table
        self.pkey = pkey
    
    def commit(self):
        "Commit transaction without requiring a appconn reference"
        appconn.commit()
    
    def rollback(self):
        "Rollback transaction without requiring a appconn reference"
        appconn.rollback()    

    def select_record(self):
        "Select a record of a table based on primay key value"
        script = "SELECT * FROM {} WHERE {};"
        script = script.format(self.table,
                               " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey]))
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(script, self)
                if cur.rowcount:
                    self.update(cur.fetchone())
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)    
            
    def insert_record(self):
        "Insert a record base on primary key"
        script = "INSERT INTO {} ({}) VALUES ({}) RETURNING {};"
        # primary key fields are always returned to self dict
        script = script.format(self.table,
                               ", ".join(self.keys()),
                               ", ".join(["%({})s ".format(i) for i in self.keys()]),
                               ", ".join([i for i in self.keys() if i not in self.pkey] + list(self.pkey)))
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(script, self)
                if cur.rowcount:
                    self.update(cur.fetchone())  
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)    
                  
    def update_record(self):
        "Update a record base on primary key, raise an exception if modified before"
        # check row_timestamp
        if 'row_timestamp' in self:
            where = " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey])
            args = {k:self[k] for k in self.pkey} # primary key fields
            args['row_timestamp'] = self['row_timestamp']
            script = "SELECT row_timestamp = %(row_timestamp)s FROM {} WHERE {};".format(self.table, where)            
            try:
                with appconn.cursor() as cur:
                    cur.execute(script, args)
                    result = cur.fetchone()[0]
                    if not result:
                        raise PyAppDBConcurrencyError()                    
            except psycopg2.Error as er:
                raise PyAppDBError(er.pgcode, er.pgerror) 
        # update
        script = "UPDATE {} SET {} WHERE {} RETURNING row_timestamp;"
        script = script.format(self.table,
                               ", ".join(["{} = %({})s".format(i, i) for i in self if i not in self.pkey]),
                               " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey]))
        print(script)
        print(self)
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(script, self)
                self['row_timestamp'] = cur.fetchone()[0]
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)    
            
    def delete_record(self):
        "Delete one record base on primary key, raise an exception if modified before"
        # check row_timestamp
        if 'row_timestamp' in self:
            where = " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey])
            args = {k:self[k] for k in self.pkey}
            script = "SELECT row_timestamp = {} FROM {} WHERE {};".format(self['row_timestamp'],
                                                                         self.table,
                                                                         where)            
            try:
                with appconn.cursor() as cur:
                    cur.execute(script, args)
                    result = cur.fetchone()[0]
                    if not result:
                        raise PyAppDBConcurrencyError()                    
            except psycopg2.Error as er:
                raise PyAppDBError(er.pgcode, er.pgerror)
        # delete
        script = "DELETE FROM {} WHERE {}"
        script = script.format(self.table,
                               " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey]))
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(script, self)
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)
            

class RecordSet(list):
    """A list of record of a database table. Each record is a Record instance"""

    def __init__(self, table, pkey = None):
        """table = database table
           pkey = list of primary key fields"""
        self.table = table
        self.pkey = pkey
    
    def insert_records(self):
        "Insert a list of records"
        if not self: return # empty list, nothing to do
        script = "INSERT INTO {} ({}) VALUES ({}) RETURNING {};"
        # primary key fields are always returned to self dict
        # script constructor based on the first item of the list
        script = script.format(self.table,
                               ", ".join(self[0].keys()),
                               ", ".join(["%({})s ".format(i) for i in self[0].keys()]),
                               ", ".join([i for i in self[0].keys() if i not in self.pkey] + list(self.pkey)))
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                for r in self:
                    cur.execute(script, r)
                    r.update(cur.fetchone())  
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)    

    def select_records(self):
        "Select a record of a table based on primay key value"
        script = "SELECT * FROM {} WHERE {};"
        script = script.format(self.table,
                               " AND ".join(["{} = %({})s".format(i, i) for i in self.pkey]))
        self.clear()
        try:
            with appconn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(script, r)
                for r in self:
                    self.append(r)
        except psycopg2.Error as er:
            raise PyAppDBError(er.pgcode, er.pgerror)      



class WebOrder():
    "A order header and details"

    def __init__(self):
        self.header = Record('web_order_header', ('id',))
        self.details = RecordSet('web_order_detail', ('id',))

    def insert(self):
        "Insert everything after completed the order"
        #self.header['event'] = appconn.event
        # insert
        try:
            self.header.insert_record()
            t = self.header['id']
            #ev = self.header['event']
            for i in self.details:
                i['id_header']= t
            self.details.insert_records()
        except PyAppDBError as er:
            appconn.rollback()
            raise PyAppDBError(er)
        else:
            appconn.commit()
            return t
        