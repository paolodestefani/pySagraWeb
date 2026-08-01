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

import os
import configparser
import logging
from logging.handlers import RotatingFileHandler
import datetime
import time
import signal  # <-- Added to handle Ctrl+C properly
import sys     # <-- Added for clean process exit

from flask import Flask
from waitress import serve

from app.database.connect import appconn
from app.order_entry import order_bp 
from app.order_status import status_bp 

# start logging system with automatic size limit
# 1 MB = 1 * 1024 * 1024 bytes max 5 files of 1 MB each
max_file_size = 1 * 1024 * 1024  
logfile = os.path.join(os.getcwd(), 'logfile.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[RotatingFileHandler(logfile, maxBytes=max_file_size, backupCount=5),
                              logging.StreamHandler()])


def create_app():
    """Inizializza l'applicazione Flask, carica le configurazioni e registra i Blueprint."""
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'
    
    def format_italiano(value):
        # Se incontra un oggetto Data o Datetime, lo formatta in stile italiano
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime('%d/%m/%Y')
        # Se incontra un oggetto Time (per la colonna Ora), prende solo ore e minuti
        if isinstance(value, datetime.time):
            return value.strftime('%H:%M')
        # Se la cella è vuota (None), restituisce una stringa vuota anziché il testo "None"
        if value is None:
            return ""
        return str(value)

    # Registra il filtro nell'ambiente Jinja di Flask con il nome 'ita'
    flask_app.jinja_env.filters['ita'] = format_italiano
    
    # load configuration file
    config = configparser.ConfigParser()
    config.read('config.cfg')
    
    # DB connection parameters
    par = {
        'app_name': config['SERVERDB']['app_name'],
        'user': config['SERVERDB']['user'],
        'password': config['SERVERDB']['password'],
        'server': config['SERVERDB']['server'],
        'port': config['SERVERDB']['port'],
        'database': config['SERVERDB']['database'],
        'db_user': config['SERVERDB']['db_user'],
        'db_password': config['SERVERDB']['db_password'],
        'hostname': config['SERVERDB']['hostname']
    }
    
    # Connect to database
    try:
        appconn.connect(par)
        logging.info("Database connection established")
        appconn.change_company(int(config['SERVERDB']['company']))
        logging.info("Company set to %s", config['SERVERDB']['company'])
    except Exception as e:
        print(f"Error connecting to database: {e}")
        logging.error(f"Error connecting to database: {e}")
        
    # application modules registration (Blueprint)
    flask_app.register_blueprint(order_bp)
    flask_app.register_blueprint(status_bp, url_prefix='/monitor')
    
    # return app instance and configuration
    return flask_app, config


# Handler function to manage graceful shutdown on Ctrl+C
def close_server_gracefully(signum, frame):
    print("\n**** Stopping wsgi server ****")
    logging.info("Stopping wsgi server")
    
    try:
        appconn.close()
        logging.info("Database connection closed successfully")
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")
        
    # Python will now fully respect the 3-second delay before exiting
    time.sleep(3)
    sys.exit(0)


if __name__ == '__main__':
    # Bind Ctrl+C (SIGINT) to the graceful shutdown handler
    signal.signal(signal.SIGINT, close_server_gracefully)
    
    print("**** Starting wsgi server ****")
    print("Press Ctrl+C to stop the server")
    logging.info('Starting pySagraWeb initialization')
    
    # create flask app from factory function
    app, cfg = create_app()
    
    # start WSGI server using Waitress
    serve(app, 
          host=cfg['SERVERWSGI']['host'], 
          port=int(cfg['SERVERWSGI']['port']),
          threads=int(cfg['SERVERWSGI']['threads']),
          connection_limit=int(cfg['SERVERWSGI']['connections']))
