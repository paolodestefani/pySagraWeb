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
        self._current_desk: str = "NOT SET"
        
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

    def advance(self, desk_name: str = "N/D") -> None:
        "Advances the queue number by one, rolling over to the next letter after 'Z99' back to 'A00'."
        # increase number
        self._number += 1
        if self._number == 100:
            self._number = 0
            self._letter += 1
            if self._letter == 91:
                self._letter = 65 
        self._is_new = True
        self._current_desk = desk_name

    def regress(self, desk_name: str = "N/D") -> None:
        "Regresses the queue number by one, never going below 'A00'."
        # decrease number
        self._number -= 1
        if self._number < 0:
            self._number = 99
            self._letter -= 1
            if self._letter == 64:
                self._letter = 65
                self._number = 0
        self._is_new = True
        self._current_desk = desk_name
                
    def reset(self, new_value: str, desk_name: str = "N/D") -> None:
        "Resets the queue number to a new valid value."
        # reset number
        self._from_string(new_value)
        self._is_new = True
        self._current_desk = desk_name 
        
    def current(self) -> tuple[str, bool, str]:
        "Returns the current queue number, if it's new, and the active desk."
        output = f"{chr(self._letter)}{self._number:02d}"
        res = (output, self._is_new, self._current_desk)
        self._is_new = False
        return res
    
    
# set the initial queue number to 'A00' when the application starts
queue_number = QueueNumber()


@qms_bp.route('/')
def index():
    "Renders the main queue page, displaying the current queue number."
    return render_template('qms_current.html', current_text=queue_number.current())

@qms_bp.route('/get_current')
def get_current():
    "Returns the current queue number, triggers animation and plays a bell sound on change."
    number, _, desk_name = queue_number.current()
    
    effect = "pulse" # pulse or blink 
    # Generiamo l'URL corretto per il file audio usando url_for di Flask
    audio_url = url_for('static', filename='audio/bell.mp3')
    
    return f"""
    {number}
    <script>
        (function() {{
            let container = document.getElementById('queue_number');
            if (container && !container.dataset.listenerRow) {{
                container.dataset.listenerRow = "true";
                
                document.body.addEventListener('htmx:beforeSwap', function(evt) {{
                    if (evt.detail.target.id === 'queue_number') {{
                        let old_num = evt.detail.target.innerText.trim();
                        let new_num = evt.detail.xhr.responseText.split('<script>')[0].trim();
                        let effect = '{effect}';

                        if (old_num !== new_num && old_num !== '...' && old_num !== '') {{
                            // 1. play sound
                            let audio = new Audio('{audio_url}');
                            audio.play().catch(e => console.log("Audio blocked by browser policy:", e));

                            // 2. graphic effect
                            evt.detail.target.classList.remove('blink-number', 'pulse-number');
                            void evt.detail.target.offsetWidth;
                            
                            if (effect === 'blink') evt.detail.target.classList.add('blink-number');
                            if (effect === 'pulse') evt.detail.target.classList.add('pulse-number');
                            
                            setTimeout(() => {{
                                evt.detail.target.classList.remove('blink-number', 'pulse-number');
                            }}, 2000);
                        }}
                    }}
                }});
            }}
        }})();
    </script>

    <div id="queue_desk" hx-swap-oob="true" class="text-warning text-uppercase fw-bold font-qms-desk pb-2">
        in {desk_name}
    </div>
    """


# manager

@qmsmanager_bp.route('/')
def manager():
    "Renders the queue management interface for advancing, regressing, and resetting the queue number."
    number, is_new, desk_name = queue_number.current()
    return render_template('qms_manager.html', current_text=number, cash_desk_name=desk_name)

@qmsmanager_bp.route('/queue_advance', methods=['POST'])
def queue_advance():
    "Advances the queue number by one and returns a 204 No Content response, used for HTMX requests."
    desk_name = session.get('cash_desk_name', 'Cassa NON impostata')
    queue_number.advance(desk_name)
    return "", 204

@qmsmanager_bp.route('/queue_regress', methods=['POST'])
def queue_regress():
    "Regresses the queue number by one and returns a 204 No Content response, used for HTMX requests."
    desk_name = session.get('cash_desk_name', 'Cassa NON impostata')
    queue_number.regress(desk_name)
    return "", 204

@qmsmanager_bp.route('/set_cash_desk_name', methods=['POST'])
def set_cash_desk_name():
    """Saves the desk name in the user's session and returns it to update the local badge."""
    # Recuperiamo il valore inviato dal prompt JS tramite hx-vals
    new_name = request.form.get('new_name', 'Cassa 1').strip()
    
    if not new_name:
        return "Cassa NON impostata"
        
    # Salviamo nella sessione privata di QUESTO browser
    session['cash_desk_name'] = new_name
    
    # Restituiamo solo il testo puro. HTMX lo metterà dentro #local-desk-badge
    return new_name


@qmsmanager_bp.route('/queue_reset', methods=['POST'])
def reset_queue():
    "Resets the queue number to a new value provided by the user via a form submission."
    new_value = request.form.get('new_value')
    # user canceled the prompt or did not enter a value, so we do not reset the queue number
    if new_value is None:
        return "", 204
    # set the queue number to the new value entered by the user
    desk_name = session.get('cash_desk_name', 'Cassa NON impostata')
    queue_number.reset(new_value.upper(), desk_name=desk_name)
    return "", 204

@qmsmanager_bp.route('/get_current')
def get_current_value():
    "Returns the current queue number as a string, used for HTMX requests to update the display."
    number, is_new, desk_name = queue_number.current()
    return f"{number} - {desk_name}"
