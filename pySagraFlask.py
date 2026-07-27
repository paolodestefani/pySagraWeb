#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (C) Paolo De Stefani
# Author: Paolo De Stefani
# Contact: paolo <at> paolodestefani <dot> it

import os
import configparser
import locale
import datetime
import logging


locale.setlocale(locale.LC_ALL, '')


from time import strftime
from flask import Flask, render_template, flash, request, redirect, url_for, session

#from database import session
from database import PyAppDatabaseException, PyAppDBConnectionError, PyAppDBError
from database.connect import appconn
from database.connect import login
from database.item import item_list, table_list
from database.weborder import WebOrder
from database.unloads import current_date
from database.unloads import current_day_part
from database.unloads import quantity_decimals
from database.unloads import stock_unloads



app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = 'SjdnUends821Jsdlkvxh391ksdODnejdDw'


@app.route('/')
def index():
    return redirect(url_for('order_entry'))

@app.route("/ordine", methods=['GET', 'POST'])
def order_entry():
    "Create the web order form"
    # serve in caso di proxy
    #if request.headers.getlist("X-Forwarded-For"):
        #ip = request.headers.getlist("X-Forwarded-For")[0]
    #else:
        #ip = request.remote_addr
    logging.info('Web order request from %s', request.remote_addr)

    if session.get('order_id'):  # order already generated
        return redirect(url_for('order_confirmed'))

    if request.method == 'POST':
        if 'reset' in request.form:
            session.clear()  # clear session before go back to new order
            return redirect(url_for('order_entry'))

    if request.method == 'POST':
        session['delivery'] = request.form.get('delivery', 'Tavolo')
        session['table'] = request.form.get('table', '')
        session['customer'] = request.form.get('customer', '')
        session['covers'] = request.form.get('covers', '')
        # update session['lines'] with inserted quantity
        for i in session['lines']:
            if str(i[0]) in request.form:
                i[2] = request.form[str(i[0])]
            else:
                i[2] = '0' # for not available items
        session['keep'] = True
        session['total'] = sum([float(i[2]) * i[3] for i in session['lines']])

        if ((session['delivery'] == 'Asporto' and
             session['customer'] != '' and
             session['total'] != 0)
            or
            (session['delivery'] == 'Tavolo' and
             #session['table'] in session['available_table'] and
             session['covers'] and
             session['total'] != 0)):
            return redirect(url_for("order_checkout"))

        if session['total'] == 0:
            flash('Selezionare almeno un articolo prima di procedere', 'warning')
        if session['delivery'] == 'Tavolo' and session['table'] == '':
            flash('Per consegna al tavolo è necessario indicare un numero di tavolo', 'warning')
        #if session['delivery'] == 'Tavolo' and session['table'] not in session['available_table']:
            #flash("E' necessario indicare un tavolo esistente", 'warning')
        if session['delivery'] == 'Tavolo' and not session['covers']:
            flash("Per consegna al tavolo è necessario indicare il numero di coperti", 'warning')
        if session['delivery'] == 'Asporto' and not session['customer']:
            flash('Per asporto è obbligatorio indicare il nome del cliente', 'warning')


    if not 'keep' in session:  # update item and table list only on first form load
        session.clear()
        session['lines'] = [[i,
                             d,
                             0,
                             float(p),
                             locale.currency(p),
                             a]
                            for i, d, p, a in item_list()]  # must be editable elements for update quantity
        #session['available_table'] = table_list()

    return render_template('order_entry.html',
                           delivery=session.get('delivery', 'T'),
                           event=appconn.event_description,
                           customer=session.get('customer', ''),
                           table=session.get('table', ''),
                           covers=session.get('covers', ''),
                           lines=session.get('lines', []))

@app.route("/verifica", methods=['GET', 'POST'])
def order_checkout():
    "Ask to proceed/go back"

    if session.get('order_id'):  # order already generated
        return redirect(url_for('order_confirmed'))

    if not 'customer' in session:  # this can happen when do a back on order_entry after order_confirmed
        return redirect(url_for('order_entry'))

    if request.method == 'POST':
        if 'confirm' in request.form:
            return redirect(url_for('order_confirmed'))
        if 'goback' in request.form:
            return redirect(url_for('order_entry'))

    # filters selected lines
    lines = [i for i in session.get('lines', []) if i[2] != '0']
    # clean input for take away
    if session['delivery'] == 'Asporto':
        session['table'] = ''
        session['covers'] = ''

    return render_template('order_checkout.html',
                           delivery=session['delivery'],
                           customer=session['customer'],
                           table=session['table'],
                           covers=session['covers'],
                           total=locale.currency(session['total']),
                           lines=lines)

@app.route("/conferma", methods=['GET', 'POST'])
def order_confirmed():
    "Proceed creating the new order or showing the last created"

    if request.method == 'POST':  # must be before insert order
        session.clear()  # clear session before go back to new order
        return redirect(url_for('order_entry'))

    if session.get('order_id'):  # order already generated
        return render_template('order_confirmed.html',
                               order_id=session['order_id'])

    if not 'customer' in session:  # this can happen when do a back on order_entry after order_confirmed
        return redirect(url_for('order_entry'))

    # insert order
    order = WebOrder()
    order.header['date_time'] = datetime.datetime.now()
    order.header['delivery'] = {'Tavolo': 'T', 'Asporto': 'A'}[session['delivery']]
    order.header['customer_name'] = session['customer']
    order.header['table_num'] = session['table'] or None
    order.header['covers'] = session['covers'] or None
    order.header['total_amount'] = session['total']
    for i in session['lines']:
        if i[2] != '0': # only quantity != 0
            line = dict()
            line['item'] = int(i[0])
            line['quantity'] = int(i[2])
            line['price'] = i[3]
            order.details.append(line)
    # SAVE
    try:
        session['order_id'] = order.insert()
    except PyAppDBError as er:
        logging.error('Error on insering web order: {}'.format(er.message))
        return
    # show order
    return render_template('order_confirmed.html',
                           order_id=session['order_id'])

@app.route("/consumi", methods=['GET', 'POST'])
def unloads():
    "Show current unloads"
    date = current_date()
    day_part = current_day_part()
    dec = 1 #quantity_decimals()
    fs = '{{:.{}f}}'.format(dec)
    lines = [(i, fs.format(q).replace('.', ',')) for i, q in stock_unloads(date, day_part)]
    return render_template('stock_unload.html',
                           date=date.strftime('%d/%m/%Y'),
                           day_part=('Pranzo' if day_part == 'L' else 'Cena'),
                           lines=lines)


if __name__ == "__main__":
    logfile = os.path.join(os.getcwd(), 'logfile.log')
    # start logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[logging.FileHandler(logfile),
                                  logging.StreamHandler()])
    # debugging in wingide
    if 'WINGDB_ACTIVE' in os.environ:
        app.debug = False
    else:
        app.debug = True
    logging.info('Starting pySagraweb Flask Application - debug')
    # load configuration
    config = configparser.ConfigParser()
    config.read('config.cfg')
    # application login
    login(config['SERVER'])
    # run flask application
    app.run(host=config['FLASK']['host'],
            port=config['FLASK']['port'])
    #appconn.close()  # unfortunatly this will be never executed
