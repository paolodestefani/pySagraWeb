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
Queue management system for pySagraWeb

"""

from flask import Blueprint, render_template, request, session, redirect, url_for


qms_bp = Blueprint('qms', __name__)

qmsmanager_bp = Blueprint('qmsmanager', __name__)


@qmsmanager_bp.before_request
def check_authentication():
    if not session.get('authenticated'):
        return redirect(url_for('login.login', next=request.url))


class QueueNumber:
    """A queue number is a one alphabetical character ['A'..'Z'] + 2 digit number [0..99]
    
    This class provides methods to manage the queue number, including advancing, regressing, resetting,
    and retrieving the current value.
    The queue number defaults to 'A00' and can be reset to any valid value in the format 'A00' to 'Z99'.
    """
    
    def __init__(self, init_value: str = 'A00') -> None:
        "Sets the initial queue number to 'A00' or a provided valid value."
        self._letter: int
        self._number: int
        self._from_string(init_value)
        self._is_new: bool = False
        
    def _from_string(self, value: str) -> None:
        "Converts a string representation of the queue number into its internal representation."
        if not value or len(value) != 3:
            value = 'A00'
        l = value[0]
        n = value[1:]
        # bounds checking for letter and number, defaulting to 'A' and '0' if invalid
        if not 65 <= ord(l) <= 90:
            l = 'A'
        self._letter = ord(l) 
        if not n.isnumeric():
            n = '0'
        self._number = int(n)

    def advance(self) -> None:
        "Advances the queue number by one, rolling over to the next letter after 'Z99' back to 'A00'."
        self._number += 1
        if self._number == 100:
            self._number = 0
            self._letter += 1
            if self._letter == 91:
                self._letter = 65 
        self._is_new = True

    def regress(self) -> None:
        "Regresses the queue number by one, never going below 'A00'."
        self._number -= 1
        if self._number < 0:
            self._number = 99
            self._letter -= 1
            if self._letter == 64:
                self._letter = 65
                self._number = 0
        self._is_new = True
                
    def reset(self, new_value: str) -> None:
        "Resets the queue number to a new valid value."
        self._from_string(new_value)
        self._is_new = True
        
    def current(self) -> tuple[str, bool]:
        "Returns the current queue number as a string in the format 'A00'."
        output = f"{chr(self._letter)}{self._number:02d}", self._is_new
        self._is_new = False
        return output
    
    
# set the initial queue number to 'A00' when the application starts
queue_number = QueueNumber()


@qms_bp.route('/')
def index():
    "Renders the main queue page, displaying the current queue number."
    return render_template('qms_current.html', current_text='')

@qms_bp.route('/get-current')
def get_current():
    "Returns the current queue number as a string, used for HTMX requests to update the display."
    number, is_new = queue_number.current()
    if is_new:
        return f'<div class="pulse-number">{number}</div>' 
    return f'<div>{number}</div>'


# manager

@qmsmanager_bp.route('/')
def manager():
    "Renders the queue management interface for advancing, regressing, and resetting the queue number."
    return render_template('qms_manager.html')

@qmsmanager_bp.route('/queue-advance', methods=['POST'])
def queue_advance():
    "Advances the queue number by one and returns a 204 No Content response, used for HTMX requests."
    queue_number.advance()
    return "", 204

@qmsmanager_bp.route('/queue-regress', methods=['POST'])
def queue_regress():
    "Regresses the queue number by one and returns a 204 No Content response, used for HTMX requests."
    queue_number.regress()
    return "", 204

@qmsmanager_bp.route('/queue-reset', methods=['POST'])
def reset_queue():
    "Resets the queue number to a new value provided by the user via a form submission."
    new_value = request.form.get('new_value')
    # user canceled the prompt or did not enter a value, so we do not reset the queue number
    if new_value is None:
        return "", 204
    # set the queue number to the new value entered by the user
    queue_number.reset(new_value)
    return "", 204
