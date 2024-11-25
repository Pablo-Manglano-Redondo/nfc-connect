# app/routes.py

import os
import openai
from flask import abort, current_app, jsonify, render_template, request, redirect, flash, url_for, g
from flask_mail import Message
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from app import app, mail, db
from app.models import Cart, CartItem, NewsletterSubscription, User, Product, UserLink  
from app.forms import ContactForm, NewsletterForm, ProductForm, RegistrationForm, LoginForm, LogoutForm, DeleteAccountForm, UserLinkForm
from app.utils import url_for_locale, admin_required  # Asegúrate de tener admin_required en utils.py
from flask_dance.contrib.google import google
from werkzeug.utils import secure_filename

# Configura tu clave de API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

csrf = CSRFProtect(app)

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

@app.route('/privacy')
@app.route('/<lang_code>/privacy')
def privacy(lang_code=None):
    return render_template('privacy_policy.html')

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: CONTACTO-------------------------
#------------------------------------------------------------------------

@app.route('/contact', methods=['GET', 'POST'])
@app.route('/<lang_code>/contact', methods=['GET', 'POST'])
def contact_page(lang_code=None):
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
            recipients=[current_app.config['MAIL_DEFAULT_SENDER']]
        )
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
#------------------------FUNCIONALIDAD: SUSCRIPCIÓN NEWSLETTER------------
#------------------------------------------------------------------------

@app.route('/subscribe', methods=['POST'])
def subscribe():
    form = NewsletterForm()
    if form.validate_on_submit():
        email = form.email.data
        # Verificar si el email ya está suscrito
        existing_subscription = NewsletterSubscription.query.filter_by(email=email).first()
        if existing_subscription:
            flash('Ya estás suscrito a nuestra newsletter.', 'info')
        else:
            subscription = NewsletterSubscription(email=email)
            db.session.add(subscription)
            db.session.commit()
            flash('¡Te has suscrito exitosamente a nuestra newsletter!', 'success')
    else:
        flash('Por favor, ingresa un correo electrónico válido.', 'danger')
    return redirect(url_for_locale('index', lang=g.lang_code))

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: CHATBOT--------------------------
#------------------------------------------------------------------------

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    user_message = data.get('message')

    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': user_message}]
        )
        bot_message = response.choices[0].message['content']
        return jsonify({'reply': bot_message})
    except Exception as e:
        print(e)
        return jsonify({'reply': 'Lo siento, ha ocurrido un error.'}), 500

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: CARRITO--------------------------
#------------------------------------------------------------------------

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
#------------------------FUNCIONALIDAD: PRODUCTOS------------------------
#------------------------------------------------------------------------

@app.route('/admin/productos', methods=['GET'])
@login_required
@admin_required  # Asegúrate de implementar este decorador
def list_products():
    products = Product.query.all()
    return render_template('admin/list_products.html', products=products)

@app.route('/admin/productos/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        if form.image.data:
            image_file = save_image(form.image.data)
        else:
            image_file = 'default_product.jpg'
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_file=image_file
        )
        db.session.add(product)
        db.session.commit()
        flash('Producto agregado exitosamente!', 'success')
        return redirect(url_for('list_products'))
    return render_template('admin/add_product.html', form=form)

@app.route('/admin/productos/editar/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    if form.validate_on_submit():
        if form.image.data:
            image_file = save_image(form.image.data)
            product.image_file = image_file
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        db.session.commit()
        flash('Producto actualizado exitosamente!', 'success')
        return redirect(url_for('list_products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
    return render_template('admin/edit_product.html', form=form, product=product)

@app.route('/admin/productos/eliminar/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Producto eliminado exitosamente!', 'success')
    return redirect(url_for('list_products'))

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
        flash('¡Felicidades, ahora eres un usuario registrado!', 'success')
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
            flash('Correo electrónico o contraseña inválidos', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        flash('Has iniciado sesión exitosamente.', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form, logout_form=logout_form, delete_account_form=delete_account_form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.context_processor
def inject_logout_form():
    logout_form = LogoutForm()
    return dict(logout_form=logout_form)

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: OAUTH CON GOOGLE----------------
#------------------------------------------------------------------------

@app.route("/login/google")
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return redirect(url_for("login"))
    
    user_info = resp.json()
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])
    picture = user_info.get("picture", "default.jpg")

    # Buscar si el usuario ya existe
    user = User.query.filter_by(email=email).first()
    if user is None:
        # Crear un nuevo usuario
        user = User(username=name, email=email, profile_image=picture)
        user.set_password(os.urandom(16).hex())  # Generar una contraseña aleatoria
        db.session.add(user)
        db.session.commit()
    
    # Iniciar sesión al usuario
    login_user(user)
    flash("Has iniciado sesión exitosamente con Google.", "success")
    return redirect(url_for("index"))

#------------------------------------------------------------------------
#------------------------FUNCIONALIDAD: DASHBOARD -----------------------
#------------------------------------------------------------------------

# Ruta del Dashboard del Usuario
@app.route('/dashboard')
@login_required
def dashboard():
    user_links = UserLink.query.filter_by(owner=current_user).all()
    return render_template('dashboard.html', title='Dashboard', links=user_links)

# Ruta para Agregar un Nuevo Enlace
@app.route('/dashboard/add_link', methods=['GET', 'POST'])
@login_required
def add_link():
    form = UserLinkForm()
    if form.validate_on_submit():
        link = UserLink(
            title=form.title.data,
            url=form.url.data,
            icon=form.icon.data,
            description=form.description.data,
            owner=current_user
        )
        db.session.add(link)
        db.session.commit()
        flash('Enlace añadido exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_link.html', title='Agregar Enlace', form=form)

# Ruta para Editar un Enlace
@app.route('/dashboard/edit_link/<int:link_id>', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    link = UserLink.query.get_or_404(link_id)
    if link.owner != current_user:
        abort(403)
    form = UserLinkForm()
    if form.validate_on_submit():
        link.title = form.title.data
        link.url = form.url.data
        link.icon = form.icon.data
        link.description = form.description.data
        db.session.commit()
        flash('Enlace actualizado exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.title.data = link.title
        form.url.data = link.url
        form.icon.data = link.icon
        form.description.data = link.description
    return render_template('edit_link.html', title='Editar Enlace', form=form, link=link)

# Ruta para Eliminar un Enlace
@app.route('/dashboard/delete_link/<int:link_id>', methods=['POST'])
@login_required
def delete_link(link_id):
    link = UserLink.query.get_or_404(link_id)
    if link.owner != current_user:
        abort(403)
    db.session.delete(link)
    db.session.commit()
    flash('Enlace eliminado exitosamente!', 'success')
    return redirect(url_for('dashboard'))

# Ruta para la Página Pública de Enlaces (Clon de Linktree)
@app.route('/<string:username>')
def user_links_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    links = UserLink.query.filter_by(owner=user).all()
    return render_template('user_links.html', user=user, links=links)

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

def save_image(form_image):
    if form_image:
        filename = secure_filename(form_image.filename)
        # Generar un nombre único para evitar conflictos
        _, f_ext = os.path.splitext(filename)
        unique_filename = os.urandom(8).hex() + f_ext
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        form_image.save(image_path)
        return unique_filename
    return 'default_product.jpg'

