from flask import Flask, g, request
from flask_mail import Mail
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from config import Config
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.config.from_object(Config)

# Definir la función get_locale antes de inicializar Babel
def get_locale():
    if not g.get('lang_code', None):
        g.lang_code = request.accept_languages.best_match(app.config['LANGUAGES'])
    return g.lang_code

# Inicializar extensiones
db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)
babel = Babel(app, locale_selector=get_locale)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app import routes, utils, models

# Registrar funciones globales de Jinja
app.jinja_env.globals.update(toggle_lang_url=utils.toggle_lang_url)
app.jinja_env.globals.update(url_for_locale=utils.url_for_locale)

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))
