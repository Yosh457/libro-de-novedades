# blueprints/auth.py
import secrets
from datetime import datetime, timedelta
import pytz
from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash 

# Importamos modelos (UsuarioGlobal es clave aquí)
from models import db, Usuario, UsuarioGlobal 
# Importamos utilidades (asegúrate que es_password_segura esté en utils/__init__.py)
from utils import registrar_log, es_password_segura, enviar_correo_reseteo

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

# --- DICCIONARIO DE REDIRECCIONES (Para login normal) ---
RUTAS_POR_ROL = {
    "Admin": "admin.admin_panel",
    "Jefa Salud": "jefa_salud.panel_jefa_salud",
    "Encargado de Recinto": "recinto.panel_encargado_recinto",
    "Encargado de Unidad": "unidad.panel_encargado_unidad",
    "default": "libro.mi_libro_novedades"
}

def obtener_ruta_redireccion(usuario):
    rol_nombre = usuario.rol.nombre if usuario.rol else "default"
    endpoint = RUTAS_POR_ROL.get(rol_nombre, RUTAS_POR_ROL["default"])
    return url_for(endpoint)

# --- LOGIN Y LOGOUT ---

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(obtener_ruta_redireccion(current_user))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Autenticación GLOBAL
        identidad_global = UsuarioGlobal.query.filter_by(email=email).first()

        if identidad_global and identidad_global.check_password(password):
            # 2. Autorización LOCAL
            usuario_local = Usuario.query.filter_by(usuario_global_id=identidad_global.id).first()
            
            if usuario_local and usuario_local.activo and identidad_global.activo:
                login_user(usuario_local)
                registrar_log(accion="Inicio de Sesión", detalles=f"Usuario {usuario_local.nombre_completo} inició sesión.")
                
                # Si requiere cambio, lo mandamos a cambiar clave
                if identidad_global.cambio_clave_requerido:
                    flash('Por seguridad, debes cambiar tu contraseña ahora.', 'warning')
                    return redirect(url_for('auth.cambiar_clave'))
                
                flash(f'¡Bienvenido, {usuario_local.nombre_completo}!', 'success')
                return redirect(obtener_ruta_redireccion(usuario_local))
            else:
                flash('Credenciales correctas, pero no tienes permisos en este sistema.', 'warning')
        else:
            flash('Email o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    registrar_log(accion="Cierre de Sesión", detalles=f"Usuario {current_user.nombre_completo} cerró sesión.")
    logout_user()
    flash('Has cerrado la sesión.', 'success')
    return redirect(url_for('auth.login'))

# --- CAMBIO DE CLAVE (Estando Logueado) ---

@auth_bp.route('/cambiar_clave', methods=['GET', 'POST'])
@login_required
def cambiar_clave():
    if request.method == 'POST':
        password_nueva = request.form.get('nueva_password')
        password_confirmar = request.form.get('confirmar_password')

        if password_nueva != password_confirmar:
            flash('Las nuevas contraseñas no coinciden.', 'warning')
            return render_template('cambiar_clave.html')

        if not es_password_segura(password_nueva):
            flash('La contraseña no cumple los requisitos de seguridad.', 'warning')
            return render_template('cambiar_clave.html')

        try:
            # Actualizar GLOBALMENTE
            usuario_global = current_user.identidad
            usuario_global.password_hash = generate_password_hash(password_nueva)
            usuario_global.cambio_clave_requerido = False 
            
            db.session.commit()
            
            registrar_log(accion="Cambio de Clave", detalles=f"Usuario {current_user.nombre_completo} cambió su clave.")
            
            # --- LOGOUT FORZADO ---
            logout_user()
            flash('Contraseña actualizada correctamente. Por favor, inicia sesión de nuevo con tu nueva clave.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error cambiando clave: {e}")
            flash('Ocurrió un error al actualizar.', 'danger')

    return render_template('cambiar_clave.html')

# --- RECUPERACIÓN DE CLAVE (Token por Correo) ---

@auth_bp.route('/solicitar-reseteo', methods=['GET', 'POST'])
def solicitar_reseteo():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # BUSCAR EN GLOBAL (Porque ahí está el email real)
        usuario_global = UsuarioGlobal.query.filter_by(email=email).first()
        
        if usuario_global:
            # Generar token y expiración
            token = secrets.token_hex(16)
            chile_tz = pytz.timezone('America/Santiago')
            ahora_chile = datetime.now(chile_tz).replace(tzinfo=None)
            expiracion = ahora_chile + timedelta(hours=1)
            
            # Guardar en GLOBAL
            usuario_global.reset_token = token
            usuario_global.reset_token_expiracion = expiracion
            db.session.commit()
            
            # Enviar correo (Pasamos el objeto global, que tiene .email y .nombre_completo igual que el local)
            enviar_correo_reseteo(usuario_global, token)
            
            flash(f'Se ha enviado un enlace a {email}.', 'success')
        else:
            # Por seguridad, a veces es mejor decir "Si el correo existe, se envió..." 
            # pero mantendremos tu lógica original.
            flash(f'El correo {email} no se encuentra registrado.', 'danger')
            
        return redirect(url_for('auth.login'))
        
    return render_template('solicitar_reseteo.html')

@auth_bp.route('/resetear-clave/<token>', methods=['GET', 'POST'])
def resetear_clave(token):
    # BUSCAR EN GLOBAL POR TOKEN
    usuario_global = UsuarioGlobal.query.filter_by(reset_token=token).first()
    
    chile_tz = pytz.timezone('America/Santiago')
    ahora_chile = datetime.now(chile_tz).replace(tzinfo=None)
    
    # Validar token
    if not usuario_global or not usuario_global.reset_token_expiracion or usuario_global.reset_token_expiracion < ahora_chile:
        flash('El enlace de reseteo es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.solicitar_reseteo'))
        
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password') # Asegúrate que tu HTML usa este name
        confirmar_password = request.form.get('confirmar_password') # Asegúrate que tu HTML usa este name

        if nueva_password != confirmar_password:
             flash('Las contraseñas no coinciden.', 'warning')
             return render_template('resetear_clave.html', token=token) # Pasamos token por si acaso

        if not es_password_segura(nueva_password):
            flash('La contraseña no cumple los requisitos de seguridad.', 'danger')
            return render_template('resetear_clave.html', token=token)
            
        try:
            # Actualizar password GLOBAL
            usuario_global.password_hash = generate_password_hash(nueva_password)
            
            # Limpiar token
            usuario_global.reset_token = None
            usuario_global.reset_token_expiracion = None
            usuario_global.cambio_clave_requerido = False # Ya la cambió, así que quitamos el flag
            
            db.session.commit()
            
            flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión en todos los sistemas.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al restablecer contraseña.', 'danger')

    return render_template('resetear_clave.html')