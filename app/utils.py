import secrets
from flask import app, request, url_for, g
import os
from PIL import Image
from flask import current_app
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

def save_picture(form_picture, folder='img'):
    try:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(current_app.root_path, 'static', folder, picture_fn)

        # Ensure the directory exists
        if not os.path.exists(os.path.join(current_app.root_path, 'static', folder)):
            os.makedirs(os.path.join(current_app.root_path, 'static', folder))
            print(f"Directory created: {os.path.join(current_app.root_path, 'static', folder)}")

        # Resize image if necessary
        output_size = (500, 500)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        print(f"Picture saved at: {picture_path}")  # Debugging line
        return picture_fn
    except Exception as e:
        print(f"Error saving picture: {e}")
        return None