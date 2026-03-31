# utils/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import url_for

def get_email_template(titulo, contenido):
    """Plantilla HTML base con el estilo del Departamento de Salud."""
    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; max-width: 600px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; margin: 0 auto;">
        <div style="background-color: #275c80; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0; font-size: 20px;">{titulo}</h2>
        </div>
        <div style="padding: 20px; background-color: #ffffff;">
            {contenido}
        </div>
        <div style="background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 11px; color: #888; border-top: 1px solid #eee;">
            <p style="margin: 0;">Red de Atención Primaria de Salud Municipal - Alto Hospicio</p>
            <p style="margin: 5px 0 0;">Este es un mensaje automático, por favor no responder.</p>
        </div>
    </div>
    """

def enviar_correo_generico(destinatario, asunto, cuerpo_html):
    """Motor de envío de correos reutilizable."""
    remitente = os.getenv("EMAIL_USUARIO")
    contrasena = os.getenv("EMAIL_CONTRASENA")

    if not remitente or not contrasena:
        print("ERROR: Credenciales de correo no configuradas en .env")
        return False

    msg = MIMEMultipart()
    msg['Subject'] = asunto
    msg['From'] = formataddr(("Sistema Libro de Novedades", remitente))
    msg['To'] = destinatario

    msg.attach(MIMEText(cuerpo_html, 'html'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remitente, contrasena)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error al enviar correo '{asunto}': {e}")
        return False

def enviar_correo_reseteo(usuario, token):
    url = url_for('auth.resetear_clave', token=token, _external=True)
    contenido = f"""
        <p>Hola <strong>{usuario.nombre_completo}</strong>,</p>
        <p>Hemos recibido una solicitud para restablecer tu contraseña en el Sistema Libro de Novedades.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{url}" style="background-color: #275c80; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Restablecer Contraseña
            </a>
        </div>
        <p style="font-size: 13px; color: #666;">El enlace expirará en 1 hora.</p>
    """
    html = get_email_template("Recuperación de Contraseña", contenido)
    enviar_correo_generico(usuario.email, 'Restablecimiento de Contraseña - Libro de Novedades', html)

def enviar_correo_notificacion_comentario(comentario):
    url_sistema = url_for('auth.login', _external=True)
    funcionario = comentario.funcionario
    jefe = comentario.jefe
    
    contenido = f"""
        <p>Hola <strong>{funcionario.nombre_completo}</strong>,</p>
        <p>Has recibido un nuevo comentario de tipo <strong style="color: {'#28a745' if comentario.tipo == 'Favorable' else '#dc3545'};">{comentario.tipo}</strong> en tu Libro de Novedades.</p>
        <p><strong>Autor:</strong> {jefe.nombre_completo}</p>
        <p><strong>Folio:</strong> #{comentario.folio}</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{url_sistema}" style="background-color: #275c80; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Ingresar al Sistema para Revisar
            </a>
        </div>
    """
    html = get_email_template("Nuevo Comentario Registrado", contenido)
    enviar_correo_generico(funcionario.email, f'Nuevo Comentario en tu Libro de Novedades - Folio #{comentario.folio}', html)