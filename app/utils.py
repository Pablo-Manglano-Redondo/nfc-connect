import secrets
from flask import app, flash, redirect, request, url_for, g
import os
from PIL import Image
from functools import wraps
from flask import current_app
from flask_login import current_user
from flask_mail import Message
from app import mail

def toggle_lang_url():
    """This function is used to toggle the language code in the URL.
    - If the current language code is 'en', the function will return the URL with the language code 'es'.
    - If the current language code is 'es', the function will return the URL with no language code."""
    path = request.path
    current_lang = g.lang_code

    if current_lang == 'en':
        path = '' if len(path) == 1 else path
        path = '/es' + path
    else:
        if len(path) == 3:
            path = '/'
        else:
            path = path[3:]

    print(current_lang)
    print(path)
    return path

def url_for_locale(url, lang):
    """ This function is used to generate a URL with the specified language code.
    - The URL is generated using the Flask url_for function.
    - The language code is added to the URL as a prefix.
    - If the language code is 'en', the URL is returned as is.
    - If the language code is 'es', the URL is prefixed with '/es'."""
    out = url_for(url)

    if lang != 'en':
        if out == '/':
            out = '/es'
        else:
            out = '/es' + out
    
    return out

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
