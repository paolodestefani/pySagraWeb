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
Order status monitor

"""

# standard library
import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, request, url_for, session

# application modules
from app import appconfig
from app.database.event import get_event_from_date
from app.database.order_status import get_order_status
from app.database.inventory import get_inventory
from app.database.inventory import get_inventory_kit_menu


# decorator for checking if the user is logged in before accessing certain routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # save the requested page for redirecting after login
            return redirect(url_for('monitor.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next') or url_for('monitor.monitor_index')
    
    if request.method == 'POST':
        password_inserted = request.form.get('password')
        if password_inserted == appconfig['Monitor']['password']:
            session['authenticated'] = True
            session.permanent = True # session expires at browser close
            return redirect(next_page)
        else:
            error = "Password errata. Riprova."
            
    return render_template('monitor_login.html', error=error)

@monitor_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('monitor.login'))



@monitor_bp.route('/')
@login_required
def monitor_index():
    pwd = appconfig['Monitor']['password']
    return render_template('monitor.html')

@monitor_bp.route('/orders')
@login_required
def monitor_orders():
    event_id, _ = get_event_from_date(datetime.date.today())
    rows = int(appconfig['Monitor']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template('monitor_orders.html',
                           lines=lines)


@monitor_bp.route('/update_orders_rows')
@login_required
def monitor_orders_update_rows():
    event_id, _ = get_event_from_date(datetime.date.today())
    rows = int(appconfig['Monitor']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template("monitor_orders_rows.html", lines=lines)


@monitor_bp.route('/inventory')
@login_required
def monitor_inventory():
    event_id, _ = get_event_from_date(datetime.date.today())
    lines_normal = get_inventory(event_id)
    lines_kit = get_inventory_kit_menu(event_id, 'K')
    lines_menu = get_inventory_kit_menu(event_id, 'M')
    return render_template('monitor_inventory.html',
                           lines_normal=lines_normal,
                           lines_kit=lines_kit,
                           lines_menu=lines_menu)


@monitor_bp.route('/update_inventory_rows')
@login_required
def monitor_inventory_update_rows():
    event_id, _ = get_event_from_date(datetime.date.today())
    lines_normal = get_inventory(event_id)
    lines_kit = get_inventory_kit_menu(event_id, 'K')
    lines_menu = get_inventory_kit_menu(event_id, 'M')
    return render_template('monitor_inventory_rows_all.html',
                           lines_normal=lines_normal,
                           lines_kit=lines_kit,
                           lines_menu=lines_menu)

