# utils/helpers.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for
from flask_login import current_user
from models import db, Log
import re

def es_password_segura(password):
    """Valida que la contraseña cumpla con los requisitos de seguridad."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password): # Busca al menos una mayúscula
        return False
    if not re.search(r"[0-9]", password): # Busca al menos un número
        return False
    return True

# --- FUNCIONES DE LÓGICA DE NEGOCIO ---

def es_superior_jerarquico(usuario_actual, funcionario_a_ver):
    """Verifica si usuario_actual es jefe directo o superior en la cadena."""
    
    # 1. Verificación directa (Padre inmediato o Segundo Jefe)
    if (funcionario_a_ver.jefe_directo_id == usuario_actual.id) or \
       (funcionario_a_ver.segundo_jefe_id == usuario_actual.id):
        return True

    # 2. Recorrido hacia arriba (Jerarquía Recursiva)
    # Nota: Solo seguimos la línea del "Jefe Principal" para evitar ciclos complejos
    jefe_actual = funcionario_a_ver.jefe_directo
    
    # Límite de seguridad para evitar bucles infinitos (max 10 niveles)
    niveles = 0
    while jefe_actual and niveles < 10:
        if jefe_actual.id == usuario_actual.id:
            return True
        jefe_actual = jefe_actual.jefe_directo
        niveles += 1
        
    return False

# --- FUNCIONES DE LOGGING ---

def registrar_log(accion, detalles=""):
    """Registra una acción en la base de datos de logs."""
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.nombre_completo if current_user.is_authenticated else "Sistema"
    
    try:
        nuevo_log = Log(
            usuario_id=user_id,
            usuario_nombre=user_name,
            accion=accion,
            detalles=detalles
        )
        db.session.add(nuevo_log)
        db.session.commit()
    except Exception as e:
        print(f"Error al registrar log: {e}")
        db.session.rollback()

# --- FUNCIONES DE CORREO ---

def enviar_correo_reseteo(usuario, token):
    remitente = os.getenv("EMAIL_USUARIO")
    contrasena = os.getenv("EMAIL_CONTRASENA")
    
    if not remitente or not contrasena:
        print("ERROR: Credenciales de correo no configuradas en .env")
        return

    msg = MIMEMultipart()
    msg['Subject'] = 'Restablecimiento de Contraseña'
    msg['From'] = f"Sistema Libro de Novedades <{remitente}>"
    msg['To'] = usuario.email
    
    # Apunta a la ruta local auth.resetear_clave (temporalmente hasta migrar todo al portal)
    url_reseteo = url_for('auth.resetear_clave', token=token, _external=True)
    
    cuerpo_html = f"""
    <p>Hola {usuario.nombre_completo},</p>
    <p>Se ha solicitado restablecer tu contraseña.</p>
    <p><a href="{url_reseteo}">Restablecer contraseña</a></p>
    """
    msg.attach(MIMEText(cuerpo_html, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, contrasena)
            server.send_message(msg)
    except Exception as e:
        print(f"Error enviando correo: {e}")

def enviar_correo_notificacion_comentario(comentario):
    remitente = os.getenv("EMAIL_USUARIO")
    contrasena = os.getenv("EMAIL_CONTRASENA")
    
    if not remitente or not contrasena:
        return

    funcionario = comentario.funcionario
    jefe = comentario.jefe
    
    msg = MIMEMultipart()
    msg['Subject'] = f"Nueva Novedad Folio #{comentario.folio}"
    msg['From'] = f"Sistema Libro de Novedades <{remitente}>"
    msg['To'] = funcionario.email
    
    url_sistema = url_for('auth.login', _external=True)
    
    cuerpo_html = f"""
    <p>Hola {funcionario.nombre_completo},</p>
    <p>Has recibido una anotación de tipo <strong>{comentario.tipo}</strong> creada por <strong>{jefe.nombre_completo}</strong>.</p>
    <p><a href="{url_sistema}">Ver Novedad</a></p>
    """
    msg.attach(MIMEText(cuerpo_html, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, contrasena)
            server.send_message(msg)
    except Exception as e:
        print(f"Error enviando notificación: {e}")