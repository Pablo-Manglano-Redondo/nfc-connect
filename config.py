class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    # MAIL_DEFAULT_SENDER = 'info@will-soft.net'  # Reemplaza con tu correo
    MAIL_DEFAULT_SENDER = ''
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    
    LANGUAGES = ['en', 'es']  # Asegúrate de tener configurado esto si usas Flask-Babel
    
    SECRET_KEY = 'your_secret_key'  # Necesario para usar flash mensajes

