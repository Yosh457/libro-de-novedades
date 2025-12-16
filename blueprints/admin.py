# blueprints/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import or_

# Importamos modelos y utilidades
# Nota: Importamos UsuarioGlobal para el buscador
from models import db, Usuario, Rol, Unidad, Log, UsuarioGlobal
from utils import admin_required, check_password_change, registrar_log

admin_bp = Blueprint('admin', __name__, template_folder='../templates', url_prefix='/admin')

@admin_bp.route('/panel')
@login_required
@check_password_change
@admin_required
def admin_panel():
    page = request.args.get('page', 1, type=int)
    
    # Filtros
    busqueda = request.args.get('busqueda', '')
    rol_filtro = request.args.get('rol_filtro', '')
    unidad_filtro = request.args.get('unidad_filtro', '')
    estado_filtro = request.args.get('estado_filtro', '')

    # Query con JOIN para buscar por nombre global
    query = Usuario.query.join(Usuario.identidad)

    if busqueda:
        query = query.filter(
            or_(
                UsuarioGlobal.nombre_completo.ilike(f'%{busqueda}%'),
                UsuarioGlobal.email.ilike(f'%{busqueda}%')
            )
        )
    
    if rol_filtro:
        query = query.filter(Usuario.rol_id == rol_filtro)
    if unidad_filtro:
        query = query.filter(Usuario.unidad_id == unidad_filtro)
    if estado_filtro == 'activo':
        query = query.filter(Usuario.activo == True)
    elif estado_filtro == 'inactivo':
        query = query.filter(Usuario.activo == False)
    
    # Ordenar por nombre global
    pagination = query.order_by(UsuarioGlobal.nombre_completo).paginate(page=page, per_page=10, error_out=False)
    
    roles_para_filtro = Rol.query.order_by(Rol.nombre).all()
    unidades_para_filtro = Unidad.query.order_by(Unidad.nombre).all()

    return render_template('admin_panel.html', 
                        pagination=pagination,
                        roles_para_filtro=roles_para_filtro,
                        unidades_para_filtro=unidades_para_filtro,
                        busqueda=busqueda,
                        rol_filtro=rol_filtro,
                        unidad_filtro=unidad_filtro,
                        estado_filtro=estado_filtro)

# --- VINCULAR USUARIO (Antes Crear) ---
@admin_bp.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    # Solo cargamos lo necesario para el form limpio
    roles = Rol.query.order_by(Rol.nombre).all()
    
    # Jefes para el select
    jefes = Usuario.query.join(Usuario.rol).join(Usuario.identidad).filter(
        or_(
            Rol.nombre == 'Jefa Salud',
            Rol.nombre == 'Encargado de Recinto',
            Rol.nombre == 'Encargado de Unidad'
        )
    ).order_by(UsuarioGlobal.nombre_completo).all()

    if request.method == 'POST':
        usuario_global_id = request.form.get('usuario_global_id')
        rol_id = request.form.get('rol_id')
        jefe_id = request.form.get('jefe_directo_id') or None
        segundo_jefe_id = request.form.get('segundo_jefe_id') or None

        if not usuario_global_id:
            flash('Debes seleccionar un funcionario.', 'danger')
            return redirect(url_for('admin.crear_usuario'))

        if Usuario.query.filter_by(usuario_global_id=usuario_global_id).first():
            flash('Este funcionario ya está vinculado.', 'warning')
            return redirect(url_for('admin.crear_usuario'))

        # CREACIÓN LIMPIA: Solo datos locales
        nuevo_usuario = Usuario(
            usuario_global_id=usuario_global_id,
            rol_id=rol_id,
            jefe_directo_id=jefe_id,
            segundo_jefe_id=segundo_jefe_id,
            activo=True
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            usr_glob = UsuarioGlobal.query.get(usuario_global_id)
            nombre_log = usr_glob.nombre_completo if usr_glob else str(usuario_global_id)
            registrar_log("Vinculación Usuario", f"Se otorgó acceso a {nombre_log}")
            
            flash('Funcionario vinculado con éxito.', 'success')
            return redirect(url_for('admin.admin_panel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al vincular: {str(e)}', 'danger')

    # Buscador de globales (igual que antes)
    ids_locales = db.session.query(Usuario.usuario_global_id).all()
    ids_locales_lista = [id[0] for id in ids_locales]

    if ids_locales_lista:
        usuarios_disponibles = UsuarioGlobal.query.filter(
            UsuarioGlobal.id.notin_(ids_locales_lista),
            UsuarioGlobal.activo == True
        ).order_by(UsuarioGlobal.nombre_completo).all()
    else:
        usuarios_disponibles = UsuarioGlobal.query.filter_by(activo=True).order_by(UsuarioGlobal.nombre_completo).all()

    return render_template('crear_usuario.html', 
                           roles=roles, 
                           jefes=jefes,
                           usuarios_disponibles=usuarios_disponibles)

@admin_bp.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario_local = Usuario.query.get_or_404(id)
    roles = Rol.query.order_by(Rol.nombre).all()
    
    jefes = Usuario.query.join(Usuario.rol).join(Usuario.identidad).filter(
        Usuario.id != id,
        or_(
            Rol.nombre == 'Jefa Salud',
            Rol.nombre == 'Encargado de Recinto',
            Rol.nombre == 'Encargado de Unidad'
        )
    ).order_by(UsuarioGlobal.nombre_completo).all()

    if request.method == 'POST':
        # SOLO ACTUALIZAMOS ROL Y JEFES
        usuario_local.rol_id = request.form.get('rol_id')
        usuario_local.jefe_directo_id = request.form.get('jefe_directo_id') or None
        usuario_local.segundo_jefe_id = request.form.get('segundo_jefe_id') or None
        
        try:
            db.session.commit()
            registrar_log("Edición Usuario", f"Se actualizaron jerarquías de {usuario_local.nombre_completo}")
            flash('Usuario actualizado con éxito.', 'success')
            return redirect(url_for('admin.admin_panel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('editar_usuario.html', 
                           usuario=usuario_local,
                           roles=roles, 
                           jefes=jefes)

@admin_bp.route('/toggle_activo/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_activo(id):
    usuario = Usuario.query.get_or_404(id)
    usuario.activo = not usuario.activo
    
    accion_realizada = "Activación" if usuario.activo else "Desactivación"
    detalles_log = (f"Admin {current_user.nombre_completo} (ID: {current_user.id}) realizó "
                f"{accion_realizada} del usuario {usuario.nombre_completo} (ID: {usuario.id}).")
    registrar_log(accion=f"{accion_realizada} de Usuario", detalles=detalles_log)
    db.session.commit()
    
    if usuario.activo:
        flash(f'El usuario {usuario.nombre_completo} ha sido activado.', 'success')
    else:
        flash(f'El usuario {usuario.nombre_completo} ha sido desactivado.', 'warning')
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/ver_logs')
@login_required
@check_password_change
@admin_required
def ver_logs():
    page = request.args.get('page', 1, type=int)
    usuario_filtro_id = request.args.get('usuario_id', '')
    accion_filtro = request.args.get('accion', '')

    query = Log.query.order_by(Log.timestamp.desc())

    if usuario_filtro_id:
        query = query.filter(Log.usuario_id == usuario_filtro_id)
    if accion_filtro:
        query = query.filter(Log.accion == accion_filtro)
        
    logs_pagination = query.paginate(page=page, per_page=15, error_out=False)
    todos_los_usuarios = Usuario.query.all()
    todos_los_usuarios.sort(key=lambda u: u.nombre_completo)
    
    acciones_posibles = [
        "Inicio de Sesión",
        "Cierre de Sesión",
        "Creación de Comentario",
        "Aceptación de Comentario",
        "Activación de Usuario",
        "Desactivación de Usuario"
    ]
    
    filtros_actuales = {
        'usuario_id': usuario_filtro_id,
        'accion': accion_filtro
    }

    return render_template('ver_logs.html',
                        pagination=logs_pagination,
                        todos_los_usuarios=todos_los_usuarios,
                        acciones_posibles=acciones_posibles,
                        filtros=filtros_actuales)