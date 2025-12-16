# app.py
import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, flash
from flask_wtf.csrf import CSRFError

# 1. IMPORTAMOS LAS INSTANCIAS DONDE ESTÁN DEFINIDAS
# db está en models.py
from models import db, Usuario 
# login_manager y csrf están en extensions.py
from extensions import login_manager, csrf 

def create_app():
    app = Flask(__name__)
    app.jinja_env.add_extension('jinja2.ext.do')
    load_dotenv()

    # --- CONFIGURACIÓN ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Configuración de Base de Datos MySQL (Local del Libro de Novedades)
    db_pass = os.getenv('MYSQL_PASSWORD')
    db_name = 'hoja_de_vida_db' # (O el nombre real de tu base local)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_pass}@localhost/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- INICIALIZACIÓN ---
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configuración de Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    # --- REGISTRO DE BLUEPRINTS ---
    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from blueprints.admin import admin_bp
    app.register_blueprint(admin_bp)

    from blueprints.libro import libro_bp
    app.register_blueprint(libro_bp)

    from blueprints.jefa_salud import jefa_salud_bp
    app.register_blueprint(jefa_salud_bp)

    from blueprints.recinto import recinto_bp
    app.register_blueprint(recinto_bp)

    from blueprints.unidad import unidad_bp
    app.register_blueprint(unidad_bp)

    # --- RUTAS GLOBALES ---
    @app.route('/')
    def index():
        return redirect(url_for('auth.login')) 

    # --- ERRORES ---
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('La sesión expiró. Intenta enviar el formulario de nuevo.', 'warning')
        return redirect(url_for('auth.login'))
    
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return app

# Loader de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)