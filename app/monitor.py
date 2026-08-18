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
pySagra monitor

"""

# standard library
import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, request, url_for, session

# application modules
from app.database.event import get_event_from_date
from app.database.monitor import get_inventory
from app.database.monitor import get_ordered_delivered
from app.database.monitor import get_sales_summary

monitor_bp = Blueprint('monitor', __name__)


@monitor_bp.before_request
def check_authentication():
    if not session.get('authenticated'):
        return redirect(url_for('login.login', next=request.url))


@monitor_bp.route('/')
def monitor_index():
    return render_template('monitor.html')


@monitor_bp.route('/inventory')
def monitor_inventory():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_inventory(event_id)
    return render_template('monitor_inventory.html',
                           lines=lines)


@monitor_bp.route('/update_inventory_rows')
def monitor_inventory_update_rows():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_inventory(event_id)
    return render_template('monitor_inventory_rows.html',
                           lines=lines) 
    
    
@monitor_bp.route('/ordered_delivered')
def monitor_ordered_delivered():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_ordered_delivered(event_id)
    return render_template('monitor_ordered_delivered.html',
                           lines=lines)


@monitor_bp.route('/update_ordered_delivered_rows')
def monitor_ordered_delivered_update_rows():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_ordered_delivered(event_id)
    return render_template('monitor_ordered_delivered_rows.html',
                           lines=lines) 


@monitor_bp.route('/sales_summary')
def monitor_sales_summary():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_sales_summary(event_id)
    return render_template('monitor_sales_summary.html',
                           lines=lines)


@monitor_bp.route('/update_sales_summary_rows')
def monitor_sales_summary_update_rows():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    lines = get_sales_summary(event_id)
    return render_template('monitor_sales_summary_rows.html',
                           lines=lines) 
