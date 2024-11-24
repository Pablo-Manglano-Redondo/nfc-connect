from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_image = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')

class DeleteAccountForm(FlaskForm):
    submit = SubmitField('Delete Account')

class EmptyForm(FlaskForm):
    pass

class NewsletterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')

class ContactForm(FlaskForm):
    subject = SelectField('Asunto', choices=[
        ('special_request', 'Solicitud especial'),
        ('feedback', 'Dejar una opinión'),
        ('directions', 'Cómo llegar'),
        ('other', 'Otros')
    ], validators=[DataRequired()])
    name = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[DataRequired()])
    message = TextAreaField('Mensaje', validators=[DataRequired()])
    submit = SubmitField('Enviar')