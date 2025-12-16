# utils/decorators.py
from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

# --- DECORADORES DE ROL ---

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
        roles_permitidos = ['Admin', 'Jefa Salud', 'Encargado de Unidad']
        if not current_user.is_authenticated or (current_user.rol.nombre not in roles_permitidos):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def encargado_recinto_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        roles_permitidos = ['Admin', 'Jefa Salud', 'Encargado de Recinto']
        if not current_user.is_authenticated or (current_user.rol.nombre not in roles_permitidos):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def check_password_change(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Nota: Aquí eventualmente redirigirás al Portal TICs, 
        # pero por ahora mantenemos la redirección a auth.cambiar_clave si existe la ruta local
        # o mostramos un flash message.
        if current_user.is_authenticated and current_user.cambio_clave_requerido:
            return redirect(url_for('auth.cambiar_clave'))
        return f(*args, **kwargs)
    return decorated_function