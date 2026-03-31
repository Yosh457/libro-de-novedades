# blueprints/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import pytz
import secrets
import re

# Importamos los modelos y las utilidades desde nuestra nueva carpeta utils
from models import db, Usuario
from utils import registrar_log, enviar_correo_reseteo

# Definimos el Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# --- VALIDACIONES LOCALES ---
def es_password_segura(password):
    """Exige un mínimo de 8 caracteres, al menos una mayúscula y un número."""
    if len(password) < 8: return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[0-9]", password): return False
    return True

# --- DICCIONARIO DE REDIRECCIONES (Específico del Libro de Novedades) ---
RUTAS_POR_ROL = {
    "Admin": "admin.panel",
    "Jefa Salud": "jefa_salud.panel_jefa_salud",
    "Encargado de Recinto": "recinto.panel_encargado_recinto",
    "Encargado de Unidad": "unidad.panel_encargado_unidad",
    "default": "libro.mi_libro_novedades" # Para Funcionario y cualquier otro
}

def obtener_ruta_redireccion(usuario):
    """Devuelve la URL de redirección basada en el rol del usuario."""
    if not usuario.rol:
        return url_for('auth.login')
        
    endpoint = RUTAS_POR_ROL.get(usuario.rol.nombre, RUTAS_POR_ROL["default"])
    return url_for(endpoint)

# --- RUTAS DE AUTENTICACIÓN ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Redirección si ya está logueado
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            # Verificación de cuenta inactiva
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Verificación de contraseña correcta
            if usuario.check_password(password):
                login_user(usuario)
                registrar_log(accion="Inicio de Sesión", detalles=f"Acceso exitoso: {usuario.rol.nombre} ({usuario.email})")

                # Bloqueo forzoso si requiere cambio de clave
                if usuario.cambio_clave_requerido:
                    flash('Por seguridad, debes cambiar tu contraseña inicial antes de continuar.', 'warning')
                    return redirect(url_for('auth.cambiar_clave'))
                
                flash(f'Bienvenido/a, {usuario.nombre_completo}', 'success')
                return redirect(obtener_ruta_redireccion(usuario))
            else:
                registrar_log(accion="Login Fallido", detalles=f"Contraseña incorrecta para: {email}")
        else:
            registrar_log(accion="Login Fallido", detalles=f"Email no registrado: {email}")
        
        flash('Correo electrónico o contraseña incorrectos.', 'danger')
    
    # 2. Plantilla actualizada a la nueva ruta
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    # Capturamos si el cierre fue provocado por el session_timeout.js
    reason = request.args.get('reason')

    if reason == 'timeout':
        registrar_log(
            accion="Cierre de Sesión Automático",
            detalles="Sesión cerrada por inactividad del usuario."
        )
        mensaje = 'Tu sesión ha expirado por inactividad. Por favor, ingresa nuevamente.'
        categoria = 'warning'
    else:
        registrar_log(
            accion="Cierre de Sesión",
            detalles="El usuario salió del sistema manualmente."
        )
        mensaje = 'Has cerrado sesión correctamente.'
        categoria = 'success'

    logout_user()
    flash(mensaje, categoria)

    return redirect(url_for('auth.login'))

@auth_bp.route('/cambiar_clave', methods=['GET', 'POST'])
@login_required
def cambiar_clave():
    # Si el usuario ya la cambió, lo devolvemos a su panel
    if not current_user.cambio_clave_requerido:
        return redirect(obtener_ruta_redireccion(current_user))
        
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')

        if not es_password_segura(nueva_password):
            flash('Error: La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.', 'danger')
        else:
            current_user.set_password(nueva_password)
            current_user.cambio_clave_requerido = False
            db.session.commit()
            
            registrar_log(accion="Cambio de Clave", detalles="El usuario actualizó su contraseña obligatoria.")
            logout_user()
            flash('Contraseña actualizada correctamente. Ingresa nuevamente con tu nueva clave.', 'success')
            return redirect(url_for('auth.login'))
            
    # Plantilla actualizada a la nueva ruta
    return render_template('auth/cambiar_clave.html')

@auth_bp.route('/solicitar-reseteo', methods=['GET', 'POST'])
def solicitar_reseteo():
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    if request.method == 'POST':
        email = request.form.get('email')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            token = secrets.token_hex(16)
            cl_tz = pytz.timezone('America/Santiago')
            # Expiración en 1 hora
            expiracion = datetime.now(cl_tz).replace(tzinfo=None) + timedelta(hours=1)
            
            usuario.reset_token = token
            usuario.reset_token_expiracion = expiracion
            db.session.commit()
            
            enviar_correo_reseteo(usuario, token)
            registrar_log(accion="Solicitud Reseteo", detalles=f"Se envió correo de reseteo a {email}")
            flash(f'Se ha enviado un enlace para restablecer la contraseña a {email}.', 'success')
        else:
            # Buena práctica de seguridad: no confirmar si el correo existe
            registrar_log(accion="Solicitud Reseteo Fallida", detalles=f"Intento de reseteo para email no registrado: {email}")
            flash(f'El correo electrónico no se encuentra registrado en el sistema.', 'danger')
            
        return redirect(url_for('auth.login'))
        
    # Plantilla actualizada a la nueva ruta
    return render_template('auth/solicitar_reseteo.html')

@auth_bp.route('/resetear-clave/<token>', methods=['GET', 'POST'])
def resetear_clave(token):
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    usuario = Usuario.query.filter_by(reset_token=token).first()
    cl_tz = pytz.timezone('America/Santiago')
    ahora = datetime.now(cl_tz).replace(tzinfo=None)
    
    if not usuario or not usuario.reset_token_expiracion or usuario.reset_token_expiracion < ahora:
        flash('El enlace de restablecimiento es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.solicitar_reseteo'))
        
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')

        if not es_password_segura(nueva_password):
            flash('Error: La nueva contraseña no cumple con los requisitos de seguridad.', 'danger')
        else:
            usuario.set_password(nueva_password)
            usuario.reset_token = None
            usuario.reset_token_expiracion = None
            db.session.commit()
            
            registrar_log(accion="Recuperación Clave", detalles=f"Usuario {usuario.email} recuperó su clave exitosamente.")
            flash('Tu contraseña ha sido restablecida. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        
    # Plantilla actualizada a la nueva ruta
    return render_template('auth/resetear_clave.html')