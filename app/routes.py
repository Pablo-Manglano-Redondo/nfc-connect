# app/routes.py

from collections import defaultdict
from datetime import datetime, timedelta
import os
import secrets
import openai
from flask import (
    abort, current_app, jsonify, render_template, request, redirect,
    flash, url_for, g
)
from flask_mail import Message
from flask_login import (
    login_user, logout_user, current_user, login_required
)
from flask_wtf.csrf import CSRFProtect
from flask_dance.contrib.google import google
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import app, mail, db
from app.models import (
    Cart, CartItem, ClickLog, NewsletterSubscription, ProductImage,
    User, Product, UserLink
)
from app.forms import (
    ContactForm, CustomizeForm, DeleteForm, NewsletterForm, ProductForm,
    RegistrationForm, LoginForm, LogoutForm, DeleteAccountForm,
    UserLinkForm, AddToCartForm
)
from app.utils import url_for_locale, admin_required  # Asegúrate de tener admin_required en utils.py

# -------------------------------------------------------------------
# CONFIGURACIÓN DE API Y CSRF
# -------------------------------------------------------------------

# Configura tu clave de API de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configura la protección CSRF
csrf = CSRFProtect(app)

# -------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# FUNCIONALIDAD: RUTAS PRINCIPALES
# -------------------------------------------------------------------

@app.route('/')
@app.route('/<lang_code>')
def index(lang_code=None):    
    products = Product.query.order_by(Product.date_added.desc()).limit(6).all()
    add_to_cart_form = AddToCartForm()
    
    return render_template('index.html', products=products, add_to_cart_form=add_to_cart_form)

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

@app.route('/cookies')
@app.route('/<lang_code>/cookies')
def cookies(lang_code=None):
    return render_template('cookies.html')

@app.route('/privacy')
@app.route('/<lang_code>/privacy')
def privacy(lang_code=None):
    return render_template('privacy.html')

@app.route('/servicios/<service_slug>')
def service_detail(service_slug):
    service_templates = {
        'diseno-personalizado': 'diseno_personalizado.html',
        'integracion-linktree': 'integracion_linktree.html',
        'gestion-analisis': 'gestion_analisis.html'
    }
    template = service_templates.get(service_slug)
    if not template:
        abort(404)
    return render_template(template)

# -------------------------------------------------------------------
# FUNCIONALIDAD: CONTACTO
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# FUNCIONALIDAD: SUSCRIPCIÓN NEWSLETTER
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# FUNCIONALIDAD: CHATBOT
# -------------------------------------------------------------------

@app.route('/api_chat', methods=['POST'])
@csrf.exempt  # Exime esta ruta de la protección CSRF
def api_chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Datos inválidos'}), 400

    user_message = data['message']
    # Aquí puedes integrar la lógica de tu chatbot o usar una API externa

    # Respuesta de ejemplo
    reply = f'Recibí tu mensaje: "{user_message}". ¿En qué más puedo ayudarte?'

    return jsonify({'reply': reply}), 200

# -------------------------------------------------------------------
# FUNCIONALIDAD: CARRITO
# -------------------------------------------------------------------

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
    form = AddToCartForm()
    if form.validate_on_submit():
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
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': f'Has añadido {product.name} al carrito.'}), 200
        else:
            return redirect(request.referrer or url_for('store'))
    else:
        flash('Error al añadir el producto al carrito. Por favor, intenta de nuevo.', 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Formulario inválido.'}), 400
        else:
            return redirect(request.referrer or url_for('store'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@csrf.exempt
@login_required
def remove_from_cart(product_id):
    cart = current_user.cart
    if not cart:
        flash('Tu carrito está vacío.', 'info')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'El carrito está vacío.'}), 400
        else:
            return redirect(url_for('store'))
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Producto eliminado del carrito.', 'success')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Producto eliminado del carrito.'}), 200
        else:
            return redirect(url_for('cart_view'))
    else:
        flash('Producto no encontrado en el carrito.', 'warning')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Producto no encontrado en el carrito.'}), 404
        else:
            return redirect(url_for('cart_view'))

@app.route('/checkout')
@login_required
def checkout():
    # Implementa la lógica de checkout aquí (por ejemplo, integración con pasarelas de pago)
    flash('Proceso de pago no implementado aún.', 'info')
    return redirect(url_for('cart_view'))

# -------------------------------------------------------------------
# FUNCIONALIDAD: PRODUCTOS
# -------------------------------------------------------------------

@app.route('/admin', methods=['GET'])
@login_required
@admin_required
def list_products():
    products = Product.query.all()
    delete_form = DeleteForm()
    return render_template('admin/list_products.html', products=products, delete_form=delete_form)

@app.route('/producto/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    features_list = product.get_features_list()  # Obtener la lista de características
    return render_template('product_detail.html', product=product, features_list=features_list)

@app.route('/admin/productos/agregar', methods=['GET', 'POST'])
@login_required
@admin_required  # Asegúrate de tener este decorador
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Manejar la imagen principal
        if form.image.data:
            image_file = save_image(form.image.data)
        else:
            image_file = 'default_product.jpg'
        
        # Crear el producto
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_file=image_file
        )
        
        # Establecer las características
        features_input = form.features.data  # Suponiendo que es una cadena separada por comas
        features_list = [feature.strip() for feature in features_input.split(',') if feature.strip()]
        product.set_features_list(features_list)  # Serializar y asignar
        
        db.session.add(product)
        db.session.commit()
        
        # Manejar imágenes adicionales
        if form.additional_images.data:
            for file in form.additional_images.data:
                if file:
                    additional_image = save_image(file)
                    product_image = ProductImage(image_file=additional_image, product_id=product.id)
                    db.session.add(product_image)
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
        # Manejar la imagen principal
        if form.image.data:
            image_file = save_image(form.image.data)
            product.image_file = image_file
        
        # Actualizar otros campos
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        
        # Actualizar las características
        features_input = form.features.data
        features_list = [feature.strip() for feature in features_input.split(',') if feature.strip()]
        product.set_features_list(features_list)
        
        db.session.commit()
        
        # Manejar imágenes adicionales
        if form.additional_images.data:
            for file in form.additional_images.data:
                if file:
                    additional_image = save_image(file, folder='product_images')
                    product_image = ProductImage(image_file=additional_image, product_id=product.id)
                    db.session.add(product_image)
            db.session.commit()
        
        flash('Producto actualizado exitosamente!', 'success')
        return redirect(url_for('list_products'))
    elif request.method == 'GET':
        form.name.data = product.name
        form.description.data = product.description
        form.price.data = product.price
        # Convertir la lista de características a una cadena separada por comas para el formulario
        form.features.data = ', '.join(product.get_features_list())
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

# -------------------------------------------------------------------
# FUNCIONALIDAD: AUTENTICACIÓN
# -------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        picture_file = save_picture(
            form.profile_image.data, 'profile_pics'
        ) if form.profile_image.data else 'default.jpg'
        user = User(
            username=form.username.data,
            email=form.email.data,
            profile_image=picture_file
        )
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
        return redirect(url_for('dashboard'))
    return render_template(
        'login.html',
        title='Login',
        form=form,
        logout_form=logout_form,
        delete_account_form=delete_account_form
    )

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

@app.context_processor
def inject_add_to_cart_form():
    form = AddToCartForm()
    return dict(add_to_cart_form=form)

# -------------------------------------------------------------------
# FUNCIONALIDAD: OAUTH CON GOOGLE
# -------------------------------------------------------------------

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
        user = User(
            username=name,
            email=email,
            profile_image=picture
        )
        user.set_password(os.urandom(16).hex())  # Generar una contraseña aleatoria
        db.session.add(user)
        db.session.commit()
    
    # Iniciar sesión al usuario
    login_user(user)
    flash("Has iniciado sesión exitosamente con Google.", "success")
    return redirect(url_for("dashboard"))

# -------------------------------------------------------------------
# FUNCIONALIDAD: DASHBOARD
# -------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener los enlaces del usuario ordenados por 'order'
    links = UserLink.query.filter_by(owner_id=current_user.id).order_by(UserLink.order).all()
    
    # Clicks por enlace
    clicks_per_link = {
        'labels': [link.title for link in links],
        'data': [link.clicks for link in links]
    }

    # Obtener la fecha de hoy
    today = datetime.utcnow().date()

    # Estadísticas de clics
    total_clicks = sum(link.clicks for link in links)
    today_clicks = ClickLog.query.filter(
        ClickLog.link_id.in_([link.id for link in links]),
        func.date(ClickLog.timestamp) == today - timedelta(days=1)
    ).count()
    active_links = len([link for link in links if link.clicks > 0])
    daily_average = total_clicks / len(links) if links else 0

    # Enlaces más populares (top 5)
    sorted_links = sorted(links, key=lambda l: l.clicks, reverse=True)[:5]
    popular_links = {
        'labels': [link.title for link in sorted_links],
        'data': [link.clicks for link in sorted_links]
    }

    # Tendencia de clics a lo largo del tiempo (últimos 30 días)
    today = datetime.utcnow().date()
    thirty_days_ago = today - timedelta(days=29)
    date_range = [thirty_days_ago + timedelta(days=i) for i in range(30)]

    # Inicializar diccionario para contar clics por día y por enlace
    clicks_trend = defaultdict(lambda: defaultdict(int))
    for log in ClickLog.query.filter(ClickLog.timestamp >= thirty_days_ago).all():
        click_date = log.timestamp.date()
        clicks_trend[click_date][log.link.title] += 1

    # Preparar datos para la gráfica
    trend_labels = [date.strftime('%d-%m') for date in date_range]
    datasets = []
    for link in links:
        link_data = [clicks_trend[date][link.title] for date in date_range]
        # Generar colores únicos para cada enlace
        color = generate_random_color()  # Implementa esta función o define una lista de colores
        datasets.append({
            'title': link.title,
            'data': link_data,
            'color': color
        })

    click_trend = {
        'labels': trend_labels,
        'datasets': datasets
    }

    analytics_data = {
        'clicks_per_link': clicks_per_link,
        'popular_links': popular_links,
        'click_trend': click_trend,
        'total_clicks': total_clicks,
        'today_clicks': today_clicks,
        'active_links': active_links,
        'daily_average': daily_average
    }

    return render_template('dashboard.html', links=links, analytics_data=analytics_data)

def generate_random_color():
    import random
    return 'rgba({},{},{},1)'.format(random.randint(0,255), random.randint(0,255), random.randint(0,255))

@app.route('/dashboard/customize', methods=['POST'])
@login_required
def customize():
    form = CustomizeForm()
    if form.validate_on_submit():
        # Manejar el tipo de fondo
        background_type = form.background_type.data
        if background_type in ['image', 'video']:
            current_user.background_type = background_type

        # Manejar Imagen de Fondo
        if form.background_image.data and background_type == 'image':
            image_file = save_background(form.background_image.data, 'img/backgrounds')
            current_user.background_image = image_file
            current_user.background_video = None  # Eliminar video si se selecciona imagen

        # Manejar Video de Fondo
        if form.background_video.data and background_type == 'video':
            video_file = save_background(form.background_video.data, 'video/backgrounds')
            current_user.background_video = video_file
            current_user.background_image = None  # Eliminar imagen si se selecciona video

        # Manejar Color de Enlaces
        if form.link_color.data:
            current_user.link_color = form.link_color.data

        # Manejar Biografía
        bio = form.bio.data
        if bio is not None:
            current_user.bio = bio

        # Foto de Perfil
        if form.profile_image.data:
            picture_file = save_picture(form.profile_image.data)
            current_user.profile_image = picture_file

        db.session.commit()
        flash('Personalización actualizada exitosamente!', 'success')
        return redirect(url_for('dashboard'))
    else:
        if request.method == 'POST':
            current_app.logger.debug("Formulario inválido:", form.errors)  # Depuración
    flash('Error al actualizar la personalización.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/dashboard/update_background_type', methods=['POST'])
@login_required
def update_background_type():
    data = request.get_json()
    background_type = data.get('background_type')

    if background_type not in ['image', 'video']:
        return jsonify({'success': False, 'message': 'Tipo de fondo inválido.'}), 400

    current_user.background_type = background_type
    db.session.commit()

    return jsonify({'success': True}), 200

@app.route('/dashboard/update_order', methods=['POST'])
@login_required
def update_link_order():
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'success': False}), 400
    order = data['order']  # Lista de IDs de enlaces en el nuevo orden
    try:
        for index, link_id in enumerate(order):
            link = UserLink.query.filter_by(id=int(link_id), owner=current_user).first()
            if link:
                link.order = index
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error('Error al actualizar el orden de los enlaces: %s', e)
        return jsonify({'success': False}), 500
    
@app.route('/dashboard/add_link_ajax', methods=['POST'])
@login_required
def add_link_ajax():
    form = UserLinkForm()
    if form.validate_on_submit():
        link = UserLink(
            title=form.title.data,
            url=form.url.data,
            icon=form.icon.data,
            owner=current_user
        )
        db.session.add(link)
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'errors': form.errors}), 400
    
@app.route('/dashboard/edit_link_ajax', methods=['POST'])
@login_required
def edit_link_ajax():
    form = UserLinkForm()
    link_id = request.form.get('link_id')
    link = UserLink.query.get_or_404(link_id)
    if link.owner != current_user:
        abort(403)
    if form.validate_on_submit():
        link.title = form.title.data
        link.url = form.url.data
        link.icon = form.icon.data
        db.session.commit()
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'errors': form.errors}), 400

@app.route('/dashboard/delete_link_ajax', methods=['POST'])
@login_required
def delete_link_ajax():
    data = request.get_json()
    link_id = data.get('link_id')
    link = UserLink.query.get_or_404(link_id)
    if link.owner != current_user:
        abort(403)
    db.session.delete(link)
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    theme = data.get('theme')
    if theme not in ['light', 'dark']:
        return jsonify({'success': False, 'message': 'Tema inválido.'}), 400
    current_user.theme = theme
    db.session.commit()
    return jsonify({'success': True}), 200

# Ruta para la Página Pública de Enlaces con Prefijo /user/
@app.route('/linktree/<username>')
def user_links_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    links = UserLink.query.filter_by(owner=user).order_by(UserLink.order).all()
    return render_template('user_links.html', user=user, links=links)

@app.route('/click/<int:link_id>')
def track_click(link_id):
    link = UserLink.query.get_or_404(link_id)
    
    # Incrementar el contador de clics
    link.clicks += 1
    db.session.commit()
    
    return redirect(link.url)

@app.route('/go/<int:link_id>')
def go_link(link_id):
    link = UserLink.query.get_or_404(link_id)
    
    # Incrementar el contador total de clics
    link.clicks += 1
    
    # Registrar el clic en ClickLog
    new_click = ClickLog(link_id=link.id, timestamp=datetime.utcnow())
    db.session.add(new_click)
    
    db.session.commit()
    
    return redirect(link.url)

# -------------------------------------------------------------------
# FUNCIONALIDAD: UTILIDADES
# -------------------------------------------------------------------

def save_picture(form_picture, folder='profile_pics'):
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img', folder, picture_fn)
    form_picture.save(picture_path)
    return picture_fn

def save_image(form_image, folder='img'):
    if form_image:
        filename = secure_filename(form_image.filename)
        # Generar un nombre único para evitar conflictos
        _, f_ext = os.path.splitext(filename)
        unique_filename = os.urandom(8).hex() + f_ext
        image_path = os.path.join(app.root_path, 'static', folder, unique_filename)
        form_image.save(image_path)
        return unique_filename
    return 'default_product.jpg'

def save_background(form_file, folder_name):
    _, f_ext = os.path.splitext(form_file.filename)
    if f_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
        filename = f"{current_user.username}-foto{f_ext}"
    elif f_ext.lower() in ['.mp4', '.mov', '.avi']:
        filename = f"{current_user.username}-video{f_ext}"
    file_path = os.path.join(app.root_path, 'static', folder_name, filename)

    form_file.save(file_path)
    return filename
