# utils/decorators.py
from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def check_password_change(f):
    """Verifica si el usuario debe cambiar su contraseña obligatoriamente."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.cambio_clave_requerido:
            flash('Debes cambiar tu contraseña para continuar.', 'warning')
            return redirect(url_for('auth.cambiar_clave'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol.nombre != 'Admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def jefa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.rol.nombre not in ['Admin', 'Jefa Salud']):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def encargado_unidad_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.rol.nombre not in ['Admin', 'Jefa Salud', 'Encargado de Unidad']):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def encargado_recinto_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.rol.nombre not in ['Admin', 'Jefa Salud', 'Encargado de Recinto']):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function