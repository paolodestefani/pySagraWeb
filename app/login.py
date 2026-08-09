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
Login module for the web application's sections that require authentication.

"""

# standard library
import datetime
from functools import wraps

from flask import Blueprint, render_template, redirect, request, url_for, session

# application modules
from app import appconfig


# decorator for checking if the user is logged in before accessing certain routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            # save the requested page for redirecting after login
            return redirect(url_for('login.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


login_bp = Blueprint('login', __name__)


@login_bp.route('/', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next') or url_for('order.order_header')  # default redirect after login
    
    if request.method == 'POST':
        password_inserted = request.form.get('password')
        if password_inserted == appconfig['LOGIN']['password']:
            session['authenticated'] = True
            session.permanent = True # session expires at browser close
            return redirect(next_page)
        else:
            error = "Password errata. Riprova."
            
    return render_template('login.html', error=error)

@login_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))


