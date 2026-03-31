# utils/helpers.py
from flask_login import current_user

def es_superior_jerarquico(usuario_actual, funcionario_a_ver):
    """Verifica si un usuario es jefe directo, segundo jefe o jefe superior en la cadena."""
    # 1. Verificación directa (Padre inmediato o Segundo Jefe)
    if (funcionario_a_ver.jefe_directo_id == usuario_actual.id) or \
       (funcionario_a_ver.segundo_jefe_id == usuario_actual.id):
        return True

    # 2. Recorrido hacia arriba (Jerarquía Principal)
    jefe_actual = funcionario_a_ver.jefe_directo
    while jefe_actual:
        if jefe_actual.id == usuario_actual.id:
            return True
        jefe_actual = jefe_actual.jefe_directo
    return False

def registrar_log(accion, detalles=""):
    """
    Registra un evento en la tabla 'logs'.
    Usa Lazy Import para evitar ciclos con models.py
    """
    from models import db, Log  # Importación diferida

    try:
        user_id = None
        user_nombre = "Sistema/Anónimo"

        if current_user and current_user.is_authenticated:
            user_id = current_user.id
            user_nombre = current_user.nombre_completo

        nuevo_log = Log(
            usuario_id=user_id,
            usuario_nombre=user_nombre,
            accion=accion,
            detalles=detalles
        )
        db.session.add(nuevo_log)
        db.session.commit()
    except Exception as e:
        print(f"Error al registrar log: {e}")