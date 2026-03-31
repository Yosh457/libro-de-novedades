# blueprints/unidad.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Usuario
from utils import encargado_unidad_required, check_password_change

unidad_bp = Blueprint('unidad', __name__, template_folder='../templates', url_prefix='/encargado_unidad')

# --- PROTECCIÓN GLOBAL DEL BLUEPRINT ---
@unidad_bp.before_request
@login_required
@check_password_change
@encargado_unidad_required
def before_request():
    pass

@unidad_bp.route('/panel')
def panel_encargado_unidad():
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '')

    query = Usuario.query.filter(
        or_(
            Usuario.jefe_directo_id == current_user.id,
            Usuario.segundo_jefe_id == current_user.id
        )
    )
    
    if busqueda:
        query = query.filter(
            or_(
                Usuario.nombre_completo.ilike(f'%{busqueda}%'),
                Usuario.rut.ilike(f'%{busqueda}%')
            )
        )
    
    query = query.filter(Usuario.rol.has(nombre='Funcionario'))

    pagination = query.order_by(Usuario.nombre_completo).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Actualizado a la subcarpeta jefatura/
    return render_template('jefatura/panel_encargado_unidad.html', 
                           pagination=pagination, 
                           busqueda=busqueda)