#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (C) Paolo De Stefani
# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it

import os
import configparser
import logging
import time

from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher

from database.connect import login
from database.connect import appconn

from pySagraFlask import app


d = PathInfoDispatcher({'/': app})
server = WSGIServer(('0.0.0.0', 8080), d)


if __name__ == '__main__':
   try:
      print("**** Starting cherrypy wsgi server")
      # start logging
      logfile = os.path.join(os.getcwd(), 'logfile.log')
      logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S',
                          handlers=[logging.FileHandler(logfile),
                                    logging.StreamHandler()])
      logging.info('Starting pySagraweb Flask Application on Cherrypy server')      
      # load configuration
      config = configparser.ConfigParser()
      config.read('config.cfg')
      # application login
      login(config['SERVER'])      
      server.start()
   except KeyboardInterrupt:
      print("**** Stopping cherrypy wsgi server")
      server.stop()
      appconn.close()
      time.sleep(5)  # show log messages for 5 seconds