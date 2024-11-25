# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')  # Es recomendable usar variables de entorno
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@yourdomain.com')
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    GOOGLE_OAUTH_CLIENT_ID='tu_id_de_cliente_google'
    GOOGLE_OAUTH_CLIENT_SECRET='tu_secreto_de_cliente_google'

    LANGUAGES = ['en', 'es']  # Idiomas soportados

    # Configuraciones para la subida de imágenes
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'img')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB

    # Configuraciones de OAuth para Google
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')  # Solo para desarrollo
    GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
