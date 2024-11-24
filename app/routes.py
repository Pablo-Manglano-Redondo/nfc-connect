import os
from flask import current_app, render_template, request, redirect, flash, url_for, g
from flask_mail import Message
from flask_login import login_user, logout_user, current_user, login_required
from app import app, mail, db
from app.models import Cart, CartItem, NewsletterSubscription, User, Product  # Asegúrate de tener el modelo Product
from app.forms import ContactForm, NewsletterForm, RegistrationForm, LoginForm, LogoutForm, DeleteAccountForm
from app.utils import url_for_locale

#------------------------------------------------------------------------
#------------------------MIDDLEWARE--------------------------------------
#------------------------------------------------------------------------

@app.before_request
def parse_url():
    path = request.path
    g.lang_code = 'en'
    if path.startswith('/es'):
        g.lang_code = 'es'
    elif path.startswith('/en'):
        if len(path) == 3:
            return redirect('/', code=301)
        path = path[3:]
        return redirect(path, code=301)
    return None

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: RUTAS PRINCIPALES----------------
#------------------------------------------------------------------------

@app.route('/')
@app.route('/<lang_code>')
def index(lang_code=None):    
    # Lista de videos: Puedes obtenerlos desde la base de datos o definirlos manualmente
    videos = [
        {'filename': 'cliente1.mp4', 'title': 'Cliente 1', 'description': 'Descripción breve del testimonio del cliente 1.'},
        {'filename': 'cliente2.mp4', 'title': 'Cliente 2', 'description': 'Descripción breve del testimonio del cliente 2.'},
        {'filename': 'cliente3.mp4', 'title': 'Cliente 3', 'description': 'Descripción breve del testimonio del cliente 3.'},
        {'filename': 'cliente4.mp4', 'title': 'Cliente 4', 'description': 'Descripción breve del testimonio del cliente 4.'},
        {'filename': 'cliente5.mp4', 'title': 'Cliente 5', 'description': 'Descripción breve del testimonio del cliente 5.'},
        # Agrega más videos según sea necesario
    ]
    
    return render_template('index.html', videos=videos)

@app.route('/about')
@app.route('/<lang_code>/about')
def about(lang_code=None):
    return render_template('about.html')

@app.route('/store')
@app.route('/<lang_code>/store')
def store(lang_code=None):
    # Lógica para mostrar productos
    products = Product.query.all()  # Asumiendo que tienes un modelo Product
    return render_template('store.html', products=products)

@app.route('/how_it_works')
@app.route('/<lang_code>/how_it_works')
def how_it_works(lang_code=None):
    return render_template('how_it_works.html')

@app.route('/contact')
@app.route('/<lang_code>/contact')
def contact(lang_code=None):
    return render_template('contact.html')

@app.route('/privacy')
@app.route('/<lang_code>/privacy')
def privacy(lang_code=None):
    return render_template('privacy_policy.html')

@app.route('/cart')
@app.route('/<lang_code>/cart')
@login_required
def cart_view(lang_code=None):
    cart = current_user.cart
    if not cart or not cart.cart_items:
        flash('Tu carrito está vacío.', 'info')
        return render_template('cart.html', cart_items=[], total_price=0)
    
    cart_items = cart.cart_items
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: SUSCRIPCIÓN NEWSLETTER------------
#------------------------------------------------------------------------

@app.route('/subscribe', methods=['POST'])
def subscribe():
    form = NewsletterForm()
    if form.validate_on_submit():
        email = form.email.data
        subscription = NewsletterSubscription(email=email)
        db.session.add(subscription)
        db.session.commit()
        flash('You have been successfully subscribed to our newsletter!', 'success')
    return redirect(url_for_locale('index', lang=g.lang_code))

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: CARRITO--------------------------
#------------------------------------------------------------------------

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = current_user.cart
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'Has añadido {product.name} al carrito.', 'success')
    return redirect(request.referrer or url_for('store'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = current_user.cart
    if not cart:
        flash('Tu carrito está vacío.', 'info')
        return redirect(url_for('store'))
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Producto eliminado del carrito.', 'success')
    else:
        flash('Producto no encontrado en el carrito.', 'warning')
    
    return redirect(url_for('cart_view'))

@app.route('/checkout')
@login_required
def checkout():
    # Implementa la lógica de checkout aquí (por ejemplo, integración con pasarelas de pago)
    flash('Proceso de pago no implementado aún.', 'info')
    return redirect(url_for('cart_view'))


#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: AUTENTICACIÓN--------------------
#------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.profile_image.data, 'profile_pics') if form.profile_image.data else 'default.jpg'
        user = User(username=form.username.data, email=form.email.data, profile_image=picture_file)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    logout_form = LogoutForm()
    delete_account_form = DeleteAccountForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form, logout_form=logout_form, delete_account_form=delete_account_form)

@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: CONTACTO-------------------------
#------------------------------------------------------------------------

@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    form = ContactForm()
    if form.validate_on_submit():
        subject = form.subject.data
        name = form.name.data
        email = form.email.data
        message = form.message.data
        phone = form.phone.data

        msg = Message(
            subject=f"New Contact Form Submission: {subject}",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['MAIL_DEFAULT_SENDER']])
        msg.body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"

        try:
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for_locale('contact_page', lang=g.lang_code))
        except Exception as e:
            flash('There\'s been an error sending your message. Please try again later.', 'danger')
            current_app.logger.error('Error sending mail: %s', e)
    return render_template('contact.html', form=form)

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: UTILIDADES-----------------------
#------------------------------------------------------------------------

def save_picture(form_picture, folder='profile_pics'):
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img', picture_fn)
    form_picture.save(picture_path)
    return picture_fn
