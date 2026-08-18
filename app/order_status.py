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
Order status

"""

# standard library
import datetime

from flask import Blueprint, render_template, redirect, request, url_for, session

# application modules
from app import appconfig
from app.database.event import get_event_from_date
from app.database.order_status import get_order_status


status_bp = Blueprint('status', __name__)

@status_bp.route('/')
def status_index():
    return redirect(url_for('status.order_status'))


@status_bp.route('/order_status')
def order_status():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    rows = int(appconfig['STATUS']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template('current_order_status.html',
                           lines=lines)


@status_bp.route('/update_order_status_rows')
def order_status_update_rows():
    event_id = get_event_from_date(datetime.date.today())['event_id']
    rows = int(appconfig['STATUS']['rows'])
    lines = get_order_status(event_id, rows)
    return render_template("current_order_status_rows.html", lines=lines)
