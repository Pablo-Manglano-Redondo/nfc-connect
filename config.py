class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    # MAIL_USERNAME = 'info@will-soft.net'
    # MAIL_PASSWORD = 'buoysddiasldA562334@#@#@|'
    MAIL_USERNAME = 'pmanglano@will-soft.net'
    MAIL_PASSWORD = 'Trueno369@'
    # MAIL_DEFAULT_SENDER = 'info@will-soft.net'  # Reemplaza con tu correo
    MAIL_DEFAULT_SENDER = 'pmanglano@will-soft.net'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    WEBHOOK_URL = 'https://discord.com/api/webhooks/1245767746122285158/uOQleqhrQCzvaSEbxC-RmGvso5jBsZi3784VkyPoKd8GtkfAYz7y6YDF5Ql_Nol5Id3_'
    WEBHOOK_URL2 = 'https://discordapp.com/api/webhooks/1266462008149151867/tryWrWCpTl5TjZVHxhdGbX-Umf0RXlrRyzcLPEuzRwKDfjm1rwuhvXQIW8RQmgqzlVXu'
    
    LANGUAGES = ['en', 'es']  # Asegúrate de tener configurado esto si usas Flask-Babel
    
    SECRET_KEY = 'your_secret_key'  # Necesario para usar flash mensajes

