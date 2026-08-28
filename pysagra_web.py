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
import logging
from logging.handlers import RotatingFileHandler
import datetime
import decimal
import locale
import time
import signal
import sys
from typing import Any

from flask import Flask, request, redirect, url_for
from waitress import serve

# application modules
from app import appconfig
from app import APP_NAME
from app import APP_VERSION_MAJOR
from app import APP_VERSION_MINOR
from app import APP_VERSION_PATCH
from app import FLASK_SECRET_KEY

from app import appconfig
from app.database.connect import appconn
from app.login import login_bp
from app.order_entry import order_bp 
from app.order_status import status_bp
from app.monitor import monitor_bp 
from app.queue_management import qms_bp
from app.queue_management import qmsmanager_bp


# start logging system with automatic size limit
# 1 MB = 1 * 1024 * 1024 bytes max 5 files of 1 MB each
max_file_size = 1 * 1024 * 1024  
logfile = os.path.join(os.getcwd(), 'logfile.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[RotatingFileHandler(logfile, maxBytes=max_file_size, backupCount=5),
                              logging.StreamHandler()])

    
def format_values(value: Any) -> str:
    "Flask format filter to format values for display in templates"
    # for a Date or Datetime object
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime('%x')
    # for a Time object (for the Ora column), it takes only hours and minutes
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M')
    if isinstance(value, int):
        return f"{value:n}" # format integer with thousands separator
    if isinstance(value, decimal.Decimal):
        return locale.format_string("%.2f", value, grouping=True)
    # for an empty cell (None), return an empty string instead of the text "None"
    if value is None:
        return ""
    return str(value)
    

def create_app() -> Flask:
    """Initialize the Flask application, load configurations, and save Blueprints."""
    # setting locale
    logging.info(f"Setting app locale to {appconfig['FLASKAPP']['locale']}")
    locale.setlocale(locale.LC_ALL, appconfig['FLASKAPP']['locale'])
    # create Flask app
    if getattr(sys, 'frozen', False):
        # path to the temporary folder created by PyInstaller
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        flask_app = Flask(APP_NAME, template_folder=template_folder, static_folder=static_folder)
    else:
        # standard behavior during development
        flask_app = Flask(APP_NAME)
    # # #    
    flask_app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    # register the filter in Flask's Jinja environment with the name 'fmt'
    flask_app.jinja_env.filters['fmt'] = format_values
    # DB connection parameters
    par = {
        'app_name': appconfig['SERVERDB']['app_name'],
        'app_version_major': appconfig['SERVERDB']['app_version_major'],
        'app_version_minor': appconfig['SERVERDB']['app_version_minor'],
        'pg_min_ver': appconfig['SERVERDB']['pg_min_ver'],
        'user': appconfig['SERVERDB']['user'],
        'password': appconfig['SERVERDB']['password'],
        'server': appconfig['SERVERDB']['server'],
        'port': appconfig['SERVERDB']['port'],
        'database': appconfig['SERVERDB']['database'],
        'db_user': appconfig['SERVERDB']['db_user'],
        'db_password': appconfig['SERVERDB']['db_password'],
        'hostname': appconfig['SERVERDB']['hostname']
    }
    # Connect to database
    try:
        appconn.connect(par)
        logging.info("Database connection established")
        appconn.change_company(int(appconfig['SERVERDB']['company']))
        logging.info("Company set to %s", appconfig['SERVERDB']['company'])
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
    # application modules registration (Blueprint)
    flask_app.register_blueprint(order_bp, url_prefix='/order')
    flask_app.register_blueprint(status_bp, url_prefix='/status')
    flask_app.register_blueprint(monitor_bp, url_prefix='/monitor')
    flask_app.register_blueprint(qms_bp, url_prefix='/qms')
    flask_app.register_blueprint(qmsmanager_bp, url_prefix='/qmsmanager')
    flask_app.register_blueprint(login_bp, url_prefix='/auth')
    # default route
    @flask_app.route('/')
    def index():
        return redirect(url_for('order.order_header'))
    # return app instance
    return flask_app


def close_server(signum: int, frame: Any) -> None:
    "Handler for graceful shutdown of the server on Ctrl+C (SIGINT)."
    print()
    print("\n**** Stopping wsgi server ****")
    print()
    logging.info("Stopping wsgi server")
    try:
        appconn.close()
        logging.info("Database connection closed successfully")
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")
    # the 2-second delay before exiting so any log messages can be read from console before the program terminates
    time.sleep(2)
    sys.exit(0)


if __name__ == '__main__':
    "Start Flask app and WSGI server"
    # Bind Ctrl+C (SIGINT) to the graceful shutdown handler
    signal.signal(signal.SIGINT, close_server)
    print()
    print("**** Starting WSGI server ****")
    print("Press Ctrl+C to stop the server")
    print()
    
    logging.info(f'Starting {APP_NAME} version {APP_VERSION_MAJOR}.{APP_VERSION_MINOR}.{APP_VERSION_PATCH}')
    
    # create flask app from factory function
    app = create_app()
    
    @app.before_request
    def log_client_connection():
        # esclude some log messages to avoid cluttering the log
        if request.path.startswith(('/static/', '/qms/')) or request.path.endswith(('_rows', 'get_current')):
            return
        logging.info(f"Connected client - IP: {request.remote_addr} - Request: {request.method} {request.path}")
    
    # start WSGI server using Waitress
    serve(app, 
          host=appconfig['SERVERWSGI']['host'], 
          port=int(appconfig['SERVERWSGI']['port']),
          threads=int(appconfig['SERVERWSGI']['threads']),
          connection_limit=int(appconfig['SERVERWSGI']['connections']))
