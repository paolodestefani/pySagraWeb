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

"""pySagraWeb - main application module

pySagraWeb is a web application built using Flask and Waitress, designed to provide 
order entry and order status monitoring functionalities. 
It connects to a database, handles HTTP requests, and serves web pages 
for users to interact with the system.

"""

# standard library
import os
import configparser
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time
import signal
import sys
from typing import Any

# slask
from flask import Flask
from waitress import serve

# application modules
from app import session
from app.database.connect import appconn
from app.order_entry import order_bp 
from app.monitor import monitor_bp 


# start logging system with automatic size limit
# 1 MB = 1 * 1024 * 1024 bytes max 5 files of 1 MB each
max_file_size = 1 * 1024 * 1024  
logfile = os.path.join(os.getcwd(), 'logfile.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[RotatingFileHandler(logfile, maxBytes=max_file_size, backupCount=5),
                              logging.StreamHandler()])


# load configuration file and link to session dictionary for global access
session['config'] = configparser.ConfigParser()
session['config'].read('config.cfg')
    
    
def format_values(value: Any) -> str:
    "Flask format filter to format values for display in templates"
    # for a Date or Datetime object, format it in Italian style
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime('%d/%m/%Y')
    # for a Time object (for the Ora column), it takes only hours and minutes
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M')
    # for an empty cell (None), return an empty string instead of the text "None"
    if value is None:
        return ""
    return str(value)
    

def create_app() -> Flask:
    """Initialize the Flask application, load configurations, and save Blueprints."""
    flask_app = Flask(session['app_name'])
    flask_app.config['SECRET_KEY'] = session['flask_secret_key']
    # register the filter in Flask's Jinja environment with the name 'fmt'
    flask_app.jinja_env.filters['fmt'] = format_values
    # DB connection parameters
    par = {
        'app_name': session['config']['SERVERDB']['app_name'],
        'user': session['config']['SERVERDB']['user'],
        'password': session['config']['SERVERDB']['password'],
        'server': session['config']['SERVERDB']['server'],
        'port': session['config']['SERVERDB']['port'],
        'database': session['config']['SERVERDB']['database'],
        'db_user': session['config']['SERVERDB']['db_user'],
        'db_password': session['config']['SERVERDB']['db_password'],
        'hostname': session['config']['SERVERDB']['hostname']
    }
    # Connect to database
    try:
        appconn.connect(par)
        logging.info("Database connection established")
        appconn.change_company(int(session['config']['SERVERDB']['company']))
        logging.info("Company set to %s", session['config']['SERVERDB']['company'])
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
    # application modules registration (Blueprint)
    flask_app.register_blueprint(order_bp)
    flask_app.register_blueprint(monitor_bp, url_prefix='/monitor')
    # return app instance
    return flask_app

def close_server(signum: int, frame: Any) -> None:
    "Handler for graceful shutdown of the server on Ctrl+C (SIGINT)."
    print("\n**** Stopping wsgi server ****")
    logging.info("Stopping wsgi server")
    try:
        appconn.close()
        logging.info("Database connection closed successfully")
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")
    # the 3-second delay before exiting so any log messages can be read from console before the program terminates
    time.sleep(3)
    sys.exit(0)


if __name__ == '__main__':
    # Bind Ctrl+C (SIGINT) to the graceful shutdown handler
    signal.signal(signal.SIGINT, close_server)
    
    print("**** Starting wsgi server ****")
    print("Press Ctrl+C to stop the server")
    logging.info('Starting pySagraWeb initialization')
    
    # create flask app from factory function
    app = create_app()
    
    # start WSGI server using Waitress
    serve(app, 
          host=session['config']['SERVERWSGI']['host'], 
          port=int(session['config']['SERVERWSGI']['port']),
          threads=int(session['config']['SERVERWSGI']['threads']),
          connection_limit=int(session['config']['SERVERWSGI']['connections']))
