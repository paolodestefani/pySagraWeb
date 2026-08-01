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
from app.database.event import get_event_from_date
from app.database.order_status import get_order_status


status_bp = Blueprint('order_status', __name__)

@status_bp.route('/')
def visualizza_ordini():
    event_id, _ = get_event_from_date(datetime.date.today())
    lines = get_order_status(event_id)
    return render_template('order_status.html',
                           lines=lines)


@status_bp.route('/update-table')
def update_table():
    event_id, _ = get_event_from_date(datetime.date.today())
    lines = get_order_status(event_id)
    # 2. Renderizza SOLO le righe della tabella, non tutta la pagina
    return render_template("table_rows.html", lines=lines)



