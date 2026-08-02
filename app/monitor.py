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

from flask import Blueprint, render_template, redirect, url_for

# application modules
from app import session
from app.database.event import get_event_from_date
from app.database.order_status import get_order_status
from app.database.inventory import get_inventory
from app.database.inventory import get_inventory_kit_menu


monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/orders')
def monitor_orders():
    event_id, _ = get_event_from_date(datetime.date.today())
    rows = int(session['config']['Monitor']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template('monitor_orders.html',
                           lines=lines)


@monitor_bp.route('/update_orders_rows')
def monitor_orders_update_rows():
    event_id, _ = get_event_from_date(datetime.date.today())
    rows = int(session['config']['Monitor']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template("monitor_orders_rows.html", lines=lines)


@monitor_bp.route('/inventory')
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
def monitor_inventory_update_rows():
    event_id, _ = get_event_from_date(datetime.date.today())
    lines_normal = get_inventory(event_id)
    lines_kit = get_inventory_kit_menu(event_id, 'K')
    lines_menu = get_inventory_kit_menu(event_id, 'M')
    return render_template('monitor_inventory_rows_all.html',
                           lines_normal=lines_normal,
                           lines_kit=lines_kit,
                           lines_menu=lines_menu)

