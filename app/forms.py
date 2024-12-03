# app/forms.py
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    DecimalField, MultipleFileField, StringField, PasswordField, SubmitField,
    TextAreaField, FloatField, SelectField, FileField, URLField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, ValidationError, Length,
    NumberRange, URL, Optional
)
from flask_wtf.file import FileAllowed
from app.models import User

# -------------------------------------------------------------------
# Formularios de Autenticación
# -------------------------------------------------------------------
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirma contraseña', validators=[DataRequired(), EqualTo('password')])
    profile_image = FileField('Foto de perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese correo electrónico ya está en uso. Por favor, elige otro.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')

class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Borrar Cuenta')

# -------------------------------------------------------------------
# Formularios de Gestión de Cuenta de Usuario
# -------------------------------------------------------------------
class UpdateAccountForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Length(max=150)])
    picture = FileField('Actualizar Imagen de Perfil', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'])
    ])
    submit = SubmitField('Actualizar')
    
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige otro.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Ese correo electrónico ya está en uso. Por favor, elige otro.')

class UserLinkForm(FlaskForm):
    title = StringField('Título del Enlace', validators=[DataRequired(), Length(min=2, max=150)])
    url = URLField('URL del Enlace', validators=[DataRequired(), URL()])
    icon = StringField('Icono (Opcional)', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Guardar Enlace')

# -------------------------------------------------------------------
# Formularios de Newsletter y Contacto
# -------------------------------------------------------------------
class NewsletterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Subscribe')

class ContactForm(FlaskForm):
    subject = SelectField('Asunto', choices=[
        ('special_request', 'Solicitud especial'),
        ('feedback', 'Dejar una reseña'),
        ('other', 'Otros')
    ], validators=[DataRequired()])
    name = StringField('Nombre', validators=[DataRequired(), Length(max=150)])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField('Teléfono', validators=[DataRequired(), Length(max=20)])
    message = TextAreaField('Mensaje', validators=[DataRequired()])
    submit = SubmitField('Enviar')

# -------------------------------------------------------------------
# Formularios de Gestión de Productos
# -------------------------------------------------------------------
class ProductForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    price = DecimalField('Precio', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Imagen Principal del Producto', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes JPG y PNG.')
    ])
    additional_images = MultipleFileField('Imágenes Adicionales', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes JPG y PNG.')
    ])
    features = StringField('Características (separadas por comas)', validators=[Length(max=500)])
    submit = SubmitField('Guardar Producto')

class DeleteForm(FlaskForm):
    submit = SubmitField('Eliminar')

# -------------------------------------------------------------------
# Formularios de Carrito de Compras
# -------------------------------------------------------------------
class AddToCartForm(FlaskForm):
    submit = SubmitField('Añadir al Carrito')

# -------------------------------------------------------------------
# Formularios de Personalización
# -------------------------------------------------------------------
class CustomizeForm(FlaskForm):
    background_image = FileField('Imagen de Fondo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes.')
    ])
    background_video = FileField('Video de Fondo', validators=[
        Optional(),
        FileAllowed(['mp4', 'mov', 'avi'], 'Solo se permiten videos.')
    ])
    background_type = SelectField('Tipo de Fondo', choices=[('image', 'Imagen'), ('video', 'Video')], validators=[Optional()])
    link_color = StringField('Color de los Enlaces', validators=[Optional()])
    bio = TextAreaField('Biografía', validators=[Optional()])
    profile_image = FileField('Imagen de Perfil', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes.')
    ])
    submit = SubmitField('Guardar Cambios')
