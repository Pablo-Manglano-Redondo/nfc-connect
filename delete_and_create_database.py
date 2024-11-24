from app import app, db
from app.models import User, Post  # Asegúrate de importar todos los modelos

def reset_database():
    with app.app_context():
        db.drop_all()
        print("All tables dropped.")
        db.create_all()
        print("All tables created.")

def load_initial_data():
    with app.app_context():
        admin_user = User(username='admin', email='admin@will-soft.net')
        admin_user.set_password('az.Hsr~k<RZ2#Q]D')
        db.session.add(admin_user)
        db.session.commit()
        print("Initial data loaded.")

if __name__ == "__main__":
    reset_database()
    load_initial_data()
