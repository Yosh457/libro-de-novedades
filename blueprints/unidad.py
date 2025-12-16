# blueprints/unidad.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_
# Importamos UsuarioGlobal para poder filtrar y ordenar
from models import db, Usuario, UsuarioGlobal 
from utils import encargado_unidad_required, check_password_change

unidad_bp = Blueprint('unidad', __name__, template_folder='../templates', url_prefix='/encargado_unidad')

@unidad_bp.route('/panel')
@check_password_change
@login_required
@encargado_unidad_required
def panel_encargado_unidad():
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '')

    # 1. Iniciamos la consulta uniendo con la tabla global
    query = Usuario.query.join(Usuario.identidad).filter(
        or_(
            Usuario.jefe_directo_id == current_user.id,
            Usuario.segundo_jefe_id == current_user.id
        )
    )
    
    # 2. Filtramos por datos GLOBALES (Nombre y Rut)
    if busqueda:
        query = query.filter(
            or_(
                UsuarioGlobal.nombre_completo.ilike(f'%{busqueda}%'),
                UsuarioGlobal.rut.ilike(f'%{busqueda}%')
            )
        )
    
    query = query.filter(Usuario.rol.has(nombre='Funcionario'))

    # 3. Ordenamos por columna GLOBAL
    pagination = query.order_by(UsuarioGlobal.nombre_completo).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('panel_encargado_unidad.html', 
                           pagination=pagination, 
                           busqueda=busqueda)