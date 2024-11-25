# app/forms.py
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField, FileField, URLField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange, Length, URL, Optional
from flask_wtf.file import FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_image = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Sign Up')

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
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')

class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Delete Account')

class NewsletterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Subscribe')

class ContactForm(FlaskForm):
    subject = SelectField('Asunto', choices=[
        ('special_request', 'Solicitud especial'),
        ('feedback', 'Dejar una opinión'),
        ('directions', 'Cómo llegar'),
        ('other', 'Otros')
    ], validators=[DataRequired()])
    name = StringField('Nombre', validators=[DataRequired(), Length(max=150)])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email(), Length(max=150)])
    phone = StringField('Teléfono', validators=[DataRequired(), Length(max=20)])
    message = TextAreaField('Mensaje', validators=[DataRequired()])
    submit = SubmitField('Enviar')

class ProductForm(FlaskForm):
    name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField('Descripción', validators=[DataRequired(), Length(min=10)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0.0)])
    image = FileField('Imagen del Producto', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes JPG, PNG, JPEG son permitidas.')])
    submit = SubmitField('Guardar Producto')

class UserLinkForm(FlaskForm):
    title = StringField('Título del Enlace', validators=[DataRequired(), Length(min=2, max=150)])
    url = URLField('URL del Enlace', validators=[DataRequired(), URL()])
    icon = StringField('Icono (Opcional)', validators=[Optional(), Length(max=50)])
    description = StringField('Descripción (Opcional)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Guardar Enlace')

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
