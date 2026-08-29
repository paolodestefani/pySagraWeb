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

"""
Flask application for pysagra_web
"""

import datetime
import os
import locale

from flask import Flask, Blueprint, render_template, flash, request, redirect, url_for, session
from app.database.event import get_event_from_date
from app.database.item import item_web_list
from app.database.item import get_variants
from app.database.seatmap import table_list
from app.database.department import department_web_list


qrcprefix = 'PSQRC'

locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

order_bp = Blueprint('order', __name__)


@order_bp.route('/')
def index():
    "Redirect to the first order page"
    return redirect(url_for('order.order_header'))


@order_bp.route("/header", methods=['GET', 'POST'])
def order_header():
    "Create the web order form main page"
    
    if request.method == 'POST' and 'reset' in request.form:
        session.clear()  # clear session dictionary
            
    if request.method == 'POST' and 'menu' in request.form:
        session['delivery']     = request.form.get('delivery', 'Tavolo')
        session['table']        = request.form.get('table', '')
        session['customer']     = request.form.get('customer', '')
        session['covers']       = request.form.get('covers', '')
        session['dep_index']    = 0
        
        if session['delivery'] == 'Tavolo' and session['table'] == '':
            flash('Per la consegna al tavolo è necessario indicare il numero del tavolo')
            return redirect(url_for('order.order_header'))
        if session['delivery'] == 'Tavolo' and session['table'] not in session['table_list']:
            flash('Il numero del tavolo indicato NON esiste. Correggere il numero. Altrimenti se si è sicuri che il tavolo indicato sia corretto sostituirlo con il codice *** e comunicare in cassa il tavolo corretto.')
            return redirect(url_for('order.order_header'))
        if session['delivery'] == 'Tavolo' and session['covers'] in ('0', ''):
            flash("Per la consegna al tavolo è necessario indicare il numero di coperti")
            return redirect(url_for('order.order_header'))
        if session['delivery'] == 'Asporto' and not session['customer']:
            flash('Per l\'asporto è obbligatorio indicare il nome del cliente')
            return redirect(url_for('order.order_header'))
        return redirect(url_for('order.order_menu'))
       
    if not session:  # update item and item variants only on first form load or when session is cleared
        session.update(get_event_from_date(datetime.date.today()))
        session['table_list']           = table_list() + ['***']
        session['departments']          = []
        session['dep_index']            = 0
        session['lines'] = {}
        session['variants'] = {}
        for dep in department_web_list():
            session['departments'].append(dep['description'])
            session['lines'][dep['description']] = []
            for i in item_web_list(session['event_id'], dep['department_id']):
                #print(f"item_web_list: i={i}, d={d}, p={p}, a={a}, v={v}")
                session['lines'][dep['description']].append({
                    'item': str(i['id']),                       # 0 item id as string (session dict are stored as string anyway)
                    'description': i['description'],            # 1 item description
                    'quantity': 0,                              # 2 quantity 
                    'price': float(i['price']),                 # 3 price number (for totals)
                    'price_string': locale.currency(i['price']),# 4 price as currency string
                    'is_active': i['available'],                # 5 is active
                    'has_variants': i['variants'],              # 6 has variants
                    'variants': '',                             # 7 variants description 
                    'price_delta': 0.0})                        # 8 variant price delta
                if i['variants']:
                    session['variants'][i['id']] = [{
                        'description': v['description'], 
                        'price': float(v['delta']), 
                        'price_string': '(+' + locale.currency(v['delta']) + ')' if v['delta'] != 0.0 else ''}
                                            for v in get_variants(i['id'])]   
                    #print(f"variants: i={i}, variants={session['variants'][i]}")
                    #print(get_variants(i['id']))

    return render_template('order_header.html',
                           delivery = session.get('delivery', 'T'),
                           event    = session.get('event_description', '--)'),
                           customer = session.get('customer', ''),
                           table    = session.get('table', ''),
                           covers   = session.get('covers', ''))
                           

@order_bp.route("/menu", methods=['GET', 'POST'])
def order_menu():
    "Create the selectable menu"
    
    # update session['lines'] with inserted quantity
    # index of the table row coincide with list index
    for i, l in enumerate(session['lines'][session['departments'][session['dep_index']]]):
        #print(f"i={i}, l={l}")
        if str(i) in request.form:
            l['quantity'] = int(request.form[str(i)]) 
            session.modified = True
    
    # move next on department list
    if request.method == 'POST':
        if 'next' in request.form:
            session['dep_index'] += 1
            if session['dep_index'] == len(session['departments']):
                session['dep_index'] -= 1
                return redirect(url_for('order.order_checkout'))
                
    # move previous on department list     
    if request.method == 'POST':
        if 'previous' in request.form:
            session['dep_index'] -= 1
            if session['dep_index'] < 0:
                session['dep_index'] = 0
                return redirect(url_for('order.order_header'))
                
    # move to variants selection
    if request.method == 'POST':
        if 'variants' in request.form:
            return redirect(url_for('order.order_variants', 
                index=request.form['variants']))
            
    return render_template(
        'order_menu.html',
        #test       = request.form,
        department  = session['departments'][session['dep_index']],
        lines       = session['lines'][session['departments'][session['dep_index']]])
        
    
@order_bp.route("/variants/<int:index>", methods=['GET', 'POST'])
def order_variants(index):
    "Show available variants. Index is the position on the list"
    
    item_id = session['lines'][session['departments'][session['dep_index']]][index]['item']
    item_ds = session['lines'][session['departments'][session['dep_index']]][index]['description']
    
    # cancel variants selections and go back to menu
    if request.method == 'POST':
        if 'cancel' in request.form:
            return redirect(url_for('order.order_menu'))
            
    # confirm selections adding new lines for variants
    if request.method == 'POST':
        if 'confirm' in request.form:
            # determine variants selected and price delta
            var = ' '.join([session['variants'][item_id][int(i)]['description'] for i in request.form.getlist('variantschecks')])
            prd = sum([float(session['variants'][item_id][int(i)]['price']) for i in request.form.getlist('variantschecks')])
            qty = int(request.form['quantity'])
            #if not var.strip():
            #    flash('Selezionare almeno una variante')
            #    return redirect(url_for('order_variants', index=index))
            l = session['lines'][session['departments'][session['dep_index']]][index].copy()
            #print(f"line: l={l}, var={var}, prd={prd}, qty={qty}")
            l['has_variants'] = False                       # has variants
            l['quantity'] = qty                             # quantity
            l['price'] = l['price'] + prd                   # price as number
            l['price_string'] = locale.currency(l['price']) # price as currency string
            l['description'] = l['description'] + ' ' + var # description
            l['variants'] = var #.replace(';', ' ')           # variants
            l['price_delta'] = prd                          # price delta
            session['lines'][session['departments'][session['dep_index']]].insert(index + 1, l)
            session.modified = True
            return redirect(url_for('order.order_menu'))
                
    return render_template(
        'order_variants.html',
        #test       = request.form,
        item        = item_ds,
        variants    = session['variants'].get(item_id) or [],
        quantity    = 1)
        

@order_bp.route("/checkout", methods=['GET', 'POST'])
def order_checkout():
    "Summary and ask to proceed/go back"

    #if not 'customer' in session:  # this can happen when do a back on order_header after order_confirmed
    #    return redirect(url_for('order_header'))

    if request.method == 'POST':
        if 'previous' in request.form:
            # email
            session['email'] = request.form.get('email', '')
            return redirect(url_for('order.order_menu'))
        if 'fromstart' in request.form:
            #session['dep_index'] = 0
            return redirect(url_for('order.order_header'))
        if 'confirm' in request.form:
            # email
            session['email'] = request.form.get('email', '')
            if not session['is_checked']:
                flash('Selezionare almeno un articolo')
                return redirect(url_for('order.order_checkout'))
            else:
                return redirect(url_for('order.order_barcode'))

        # filters selected lines and calc total
    total = 0.0
    lines = []
    for d in session['departments']:
        # Estrae le linee che hanno quantità diversa da zero
        ln = [l for l in session['lines'][d] if int(l['quantity']) != 0]
        
        # CRITICO: Entra nel blocco e aggiunge il reparto SOLO se 'ln' contiene elementi!
        if ln:
            lines.append({'item': 0, 'description': d}) # Aggiunge il reparto solo se popolato
            lines += ln                                 # Aggiunge le righe degli articoli
            total += sum([float(i['quantity']) * float(i['price']) for i in ln])

    if lines:
        session['is_checked'] = True
    else:
        session['is_checked'] = False
    
    # clean input for take away
    if session['delivery'] == 'Asporto':
        session['table']  = ''
        session['covers'] = ''

    return render_template('order_checkout.html',
                           #test    = lines, #session['lines']['Bar'],
                           delivery = session['delivery'],
                           customer = session['customer'],
                           table    = session['table'],
                           covers   = session['covers'],
                           total    = locale.currency(total),
                           lines    = lines,
                           email    = session.get('email', ''))


@order_bp.route("/barcode", methods=['GET', 'POST'])
def order_barcode():
    "Proceed creating the new order barcode"

    if request.method == 'POST': 
        if 'new' in request.form:
            session.clear()          # clear session before go back to new order
            return redirect(url_for('order.order_header'))
        if 'previous' in request.form:
            return redirect(url_for('order.order_checkout'))
            
    lines = []
    for d in session['departments']:
        lines += [l for l in session['lines'][d] if int(l['quantity']) != 0]

    # create QR order
    order  = qrcprefix
    # delivery
    order += ";" + {'Tavolo': 'T', 'Asporto': 'A'}[session['delivery']]
    # table
    order += ";" + session['table'] or ""
    # customer name
    order += ";" + session['customer'] #.replace(';', ' ')
    # covers
    order += ";" + session['covers'] or ""
    # email
    order += ";" + session['email'] or ""
    # item lines
    for l in lines:
        order += (
              ";" + str(l['item'])          # item id
            + ";" + str(l['variants'])      # variants
            + ";" + str(l['price_delta'])   # price delta
            + ";" + str(l['quantity'])      # quantity
            )
            
    # sanity checks
    order = order.replace("\n", " ")
    #print('Len', len(order))
    if len(order) >= 1240:
        flash("""Il QR Code da generare supera il numero di caratteri possibili per questo formato.
        Ridurre l'elenco dei prodotti e varianti scelti.
        Si ricorda che l'ordine può essere modificato in cassa""")
        return redirect(url_for('order_checkout'))
    
    # show order QR code
    return render_template('order_barcode.html',
                            order_str   = order,
                            #test        = order
                            )
                            
