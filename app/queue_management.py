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

from flask import Blueprint, render_template, url_for, render_template_string, request

qms_bp = Blueprint('qms', __name__)

queue_number = 0

def calculate_number(value):
    letter_index = 65 + (value // 100)
    letter = chr(letter_index)
    number = value % 100
    return f"{letter}{number:02d}"

def convert_in_number(queue_string):
    """
    Prende una stringa come 'B05' o 'b5' e restituisce il numero intero (105).
    Se l'input è vuoto o non valido, restituisce 0 (A00).
    """
    if not queue_string:
        return 0
        
    # Puliamo la stringa rimuovendo spazi e rendendola maiuscola (es. " b05 " -> "B05")
    clean_string = queue_string.strip().upper()
    
    # separare la Lettera dai Numeri (es. A e 99)
    if not (clean_string[0].isalpha() and clean_string[1:].isdigit()):
        return 0 # Ritorna ad A00 se l'operatore scrive testo non valido
        
    letter, number_str = clean_string[0], clean_string[1:]
    
    # Calcoliamo la base numerica della lettera (A=0, B=100, C=200, ecc.)
    base_letter = (ord(letter) - 65) * 100
    number = int(number_str)
    
    # Evitiamo che numeri sopra il 99 sballino la lettera successiva erroneamente
    if number > 99:
        number = 99
        
    return base_letter + number

@qms_bp.route('/')
def index():
    global queue_number
    return render_template('qms_index.html', numero=calculate_number(queue_number))

@qms_bp.route('/pulsantiera')
def pulsantiera():
    return render_template('qms_pulsantiera.html')

@qms_bp.route('/ottieni-card')
def ottieni_card():
    global queue_number
    return render_template_string('''
        <div class="card text-center bg-dark text-white border-primary shadow-lg col-11 col-md-8">
            <div class="card-header bg-primary text-uppercase fw-bold fs-3">STIAMO SERVENDO IL NUMERO</div>
            <div class="card-body d-flex justify-content-center align-items-center" style="min-height: 70vh;">
                <h1 class="display-numero m-0">{{ turno }}</h1>
            </div>
        </div>
    ''', turno=calculate_number(queue_number))

@qms_bp.route('/avanza-coda', methods=['POST'])
def avanza_coda():
    global queue_number
    queue_number += 1
    return "", 204

@qms_bp.route('/regredisci-coda', methods=['POST'])
def regredisci_coda():
    global queue_number
    if queue_number > 0:
        queue_number -= 1
    return "", 204

# La rotta di reset ora accetta il valore digitato nel prompt javascript
@qms_bp.route('/reset-coda', methods=['POST'])
def reset_coda():
    global queue_number
    # Recuperiamo il valore inviato da htmx
    valore_inserito = request.form.get('valore')
    
    # Se l'utente clicca su "Annulla" nel prompt del browser, non modifichiamo nulla
    if valore_inserito is None:
        return "", 204
        
    # Convertiamo la stringa scritta a mano nel nostro intero progressivo
    queue_number = convert_in_number(valore_inserito)
    return "", 204
