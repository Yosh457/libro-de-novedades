# blueprints/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

# Importamos modelos de nuestra base de datos
from models import db, Usuario, Rol, Unidad, Establecimiento, CalidadJuridica, Categoria, Log

# Importamos las utilidades limpias de nuestra nueva carpeta utils
from utils import admin_required, check_password_change, registrar_log

# Creamos el Blueprint
admin_bp = Blueprint('admin', __name__, template_folder='../templates', url_prefix='/admin')

# --- PROTECCIÓN GLOBAL DEL BLUEPRINT ---
@admin_bp.before_request
@login_required
@admin_required
@check_password_change
def before_request():
    """
    Se ejecuta antes de cada petición a cualquier ruta /admin/*.
    Garantiza que nadie sin sesión, sin rol de Admin, o con una clave 
    por cambiar pueda acceder a estas rutas.
    """
    pass

# --- RUTAS DE ADMINISTRACIÓN ---

@admin_bp.route('/panel')
def panel(): # Nombre simplificado a 'panel' siguiendo tu nuevo estándar
    """
    Vista principal del Panel de Administración.
    Muestra estadísticas rápidas y la tabla de usuarios con paginación y filtros.
    """
    page = request.args.get('page', 1, type=int)
    
    # --- Lógica de Filtros ---
    busqueda = request.args.get('busqueda', '')
    rol_filtro = request.args.get('rol_filtro', '')
    unidad_filtro = request.args.get('unidad_filtro', '')
    estado_filtro = request.args.get('estado_filtro', '')

    query = Usuario.query

    if busqueda:
        query = query.filter(
            or_(
                Usuario.nombre_completo.ilike(f'%{busqueda}%'),
                Usuario.email.ilike(f'%{busqueda}%'),
                Usuario.rut.ilike(f'%{busqueda}%') # Añadimos búsqueda por RUT por conveniencia
            )
        )
    
    if rol_filtro:
        query = query.filter(Usuario.rol_id == rol_filtro)
    if unidad_filtro:
        query = query.filter(Usuario.unidad_id == unidad_filtro)
    if estado_filtro:
        if estado_filtro == 'activo':
            query = query.filter(Usuario.activo == True)
        elif estado_filtro == 'inactivo':
            query = query.filter(Usuario.activo == False)
    
    # Paginación (10 por página)
    pagination = query.order_by(Usuario.id).paginate(page=page, per_page=10, error_out=False)
    
    roles_para_filtro = Rol.query.order_by(Rol.nombre).all()
    unidades_para_filtro = Unidad.query.order_by(Unidad.nombre).all()

    # Estadísticas Rápidas adaptadas al Libro de Novedades
    stats = {
        'total_usuarios': Usuario.query.count(),
        'usuarios_activos': Usuario.query.filter_by(activo=True).count(),
        'total_unidades': Unidad.query.count()
    }
    
    # Renderizamos apuntando a la nueva carpeta admin/
    return render_template('admin/panel.html', 
                        pagination=pagination,
                        roles_para_filtro=roles_para_filtro,
                        unidades_para_filtro=unidades_para_filtro,
                        busqueda=busqueda,
                        rol_filtro=rol_filtro,
                        unidad_filtro=unidad_filtro,
                        estado_filtro=estado_filtro,
                        stats=stats)

@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    """Formulario para registrar nuevos usuarios en el sistema."""
    if request.method == 'POST':
        rut = request.form.get('rut')
        nombre = request.form.get('nombre_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        rol_id = request.form.get('rol_id')
        unidad_id = request.form.get('unidad_id')
        establecimiento_id = request.form.get('establecimiento_id')
        calidad_id = request.form.get('calidad_id')
        categoria_id = request.form.get('categoria_id')
        
        jefe_id = request.form.get('jefe_directo_id') or None
        segundo_jefe_id = request.form.get('segundo_jefe_id') or None
        forzar_cambio = request.form.get('forzar_cambio_clave') == '1'

        # Validaciones de duplicidad
        if Usuario.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado en otro usuario.', 'danger')
            return redirect(url_for('admin.crear_usuario'))
        if Usuario.query.filter_by(rut=rut).first():
            flash('El RUT ya está registrado en el sistema.', 'danger')
            return redirect(url_for('admin.crear_usuario'))

        nuevo_usuario = Usuario(
            rut=rut,
            nombre_completo=nombre,
            email=email,
            rol_id=rol_id,
            unidad_id=unidad_id,
            establecimiento_id=establecimiento_id,
            calidad_juridica_id=calidad_id,
            categoria_id=categoria_id,
            jefe_directo_id=jefe_id,
            segundo_jefe_id=segundo_jefe_id,
        )
        nuevo_usuario.set_password(password)
        nuevo_usuario.cambio_clave_requerido = forzar_cambio
        
        db.session.add(nuevo_usuario)
        db.session.commit()

        registrar_log(accion="Creación Usuario", detalles=f"Admin creó al usuario {nombre} (RUT: {rut}).")
        flash('Usuario creado con éxito.', 'success')
        return redirect(url_for('admin.panel'))

    # Carga de catálogos para los select del formulario
    roles = Rol.query.order_by(Rol.nombre).all()
    unidades = Unidad.query.order_by(Unidad.nombre).all()
    establecimientos = Establecimiento.query.order_by(Establecimiento.nombre).all()
    calidades = CalidadJuridica.query.order_by(CalidadJuridica.nombre).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    
    # Filtro complejo para jefes
    jefes = Usuario.query.join(Usuario.rol).filter(
        or_(
            Rol.nombre == 'Jefa Salud',
            Rol.nombre == 'Encargado de Recinto',
            Rol.nombre == 'Encargado de Unidad'
        )
    ).order_by(Usuario.nombre_completo).all()

    # Renderizamos apuntando a la nueva carpeta admin/
    return render_template('admin/crear_usuario.html', 
                           roles=roles, 
                           unidades=unidades, 
                           establecimientos=establecimientos, 
                           jefes=jefes,
                           calidades=calidades, 
                           categorias=categorias)

@admin_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    """Permite modificar los datos, perfil y jerarquía de un usuario."""
    usuario_a_editar = Usuario.query.get_or_404(id)

    if request.method == 'POST':
        email_nuevo = request.form.get('email')
        rut_nuevo = request.form.get('rut')

        # Validaciones de duplicidad excluyendo al usuario actual
        if Usuario.query.filter(Usuario.email == email_nuevo, Usuario.id != id).first():
            flash('Error: Ese correo ya pertenece a otro usuario.', 'danger')
            return redirect(url_for('admin.editar_usuario', id=id))
        
        if Usuario.query.filter(Usuario.rut == rut_nuevo, Usuario.id != id).first():
            flash('Error: Ese RUT ya pertenece a otro usuario.', 'danger')
            return redirect(url_for('admin.editar_usuario', id=id))

        # Actualización
        usuario_a_editar.rut = rut_nuevo
        usuario_a_editar.nombre_completo = request.form.get('nombre_completo')
        usuario_a_editar.email = email_nuevo
        usuario_a_editar.rol_id = request.form.get('rol_id')
        usuario_a_editar.unidad_id = request.form.get('unidad_id')
        usuario_a_editar.establecimiento_id = request.form.get('establecimiento_id')
        usuario_a_editar.calidad_juridica_id = request.form.get('calidad_id')
        usuario_a_editar.categoria_id = request.form.get('categoria_id')
        
        usuario_a_editar.jefe_directo_id = request.form.get('jefe_directo_id') or None
        usuario_a_editar.segundo_jefe_id = request.form.get('segundo_jefe_id') or None
        
        usuario_a_editar.cambio_clave_requerido = request.form.get('forzar_cambio_clave') == '1'

        password = request.form.get('password')
        if password:
            usuario_a_editar.set_password(password)
        
        db.session.commit()
        registrar_log(accion="Edición Usuario", detalles=f"Admin editó el perfil de {usuario_a_editar.nombre_completo}.")
        flash('Usuario actualizado con éxito.', 'success')
        return redirect(url_for('admin.panel'))

    roles = Rol.query.order_by(Rol.nombre).all()
    unidades = Unidad.query.order_by(Unidad.nombre).all()
    establecimientos = Establecimiento.query.order_by(Establecimiento.nombre).all()
    calidades = CalidadJuridica.query.order_by(CalidadJuridica.nombre).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    jefes = Usuario.query.join(Usuario.rol).filter(
        or_(
            Rol.nombre == 'Jefa Salud',
            Rol.nombre == 'Encargado de Recinto',
            Rol.nombre == 'Encargado de Unidad'
        )
    ).order_by(Usuario.nombre_completo).all()

    # Renderizamos apuntando a la nueva carpeta admin/
    return render_template('admin/editar_usuario.html', 
                           usuario=usuario_a_editar,
                           roles=roles, 
                           unidades=unidades, 
                           establecimientos=establecimientos, 
                           calidades=calidades, 
                           categorias=categorias,
                           jefes=jefes)

@admin_bp.route('/toggle_activo/<int:id>', methods=['POST'])
def toggle_activo(id):
    """Habilita o deshabilita a un usuario. Protege al Admin de autodesactivarse."""
    usuario = Usuario.query.get_or_404(id)
    
    if usuario.id == current_user.id:
        flash('Medida de seguridad: No puedes desactivar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('admin.panel'))
        
    usuario.activo = not usuario.activo
    db.session.commit()
    
    accion_realizada = "Activación" if usuario.activo else "Desactivación"
    registrar_log(accion=f"{accion_realizada} de Usuario", detalles=f"Admin cambió el estado del usuario {usuario.nombre_completo}.")
    
    if usuario.activo:
        flash(f'El usuario {usuario.nombre_completo} ha sido activado.', 'success')
    else:
        flash(f'El usuario {usuario.nombre_completo} ha sido desactivado.', 'warning')
        
    return redirect(url_for('admin.panel'))

@admin_bp.route('/ver_logs')
def ver_logs():
    """Muestra el historial de auditoría del sistema."""
    page = request.args.get('page', 1, type=int)
    usuario_filtro_id = request.args.get('usuario_id', '')
    accion_filtro = request.args.get('accion', '')

    query = Log.query.order_by(Log.timestamp.desc())

    if usuario_filtro_id:
        query = query.filter(Log.usuario_id == usuario_filtro_id)
    if accion_filtro:
        query = query.filter(Log.accion == accion_filtro)
        
    logs_pagination = query.paginate(page=page, per_page=15, error_out=False)
    todos_los_usuarios = Usuario.query.order_by(Usuario.nombre_completo).all()
    
    # Catálogo de acciones basado en lo que realmente hay en la base de datos
    acciones_posibles = [r[0] for r in db.session.query(Log.accion).distinct().all()]
    
    filtros_actuales = {
        'usuario_id': usuario_filtro_id,
        'accion': accion_filtro
    }

    # Renderizamos apuntando a la nueva carpeta admin/
    return render_template('admin/ver_logs.html',
                        pagination=logs_pagination,
                        todos_los_usuarios=todos_los_usuarios,
                        acciones_posibles=acciones_posibles,
                        filtros=filtros_actuales)