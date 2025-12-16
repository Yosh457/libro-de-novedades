# blueprints/recinto.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_
# Importamos UsuarioGlobal
from models import db, Usuario, UsuarioGlobal
from utils import encargado_recinto_required, check_password_change

recinto_bp = Blueprint('recinto', __name__, template_folder='../templates', url_prefix='/recinto')

@recinto_bp.route('/panel')
@login_required
@check_password_change
@encargado_recinto_required
def panel_encargado_recinto():
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '')

    # 1. Join con Identidad
    query = Usuario.query.join(Usuario.identidad).filter(
        Usuario.jefe_directo_id == current_user.id,
        Usuario.rol.has(nombre='Encargado de Unidad')
    )

    # 2. Filtro usando columnas Globales
    if busqueda:
        query = query.filter(
            or_(
                UsuarioGlobal.nombre_completo.ilike(f'%{busqueda}%'),
                UsuarioGlobal.rut.ilike(f'%{busqueda}%')
            )
        )

    # 3. Orden using columna Global
    encargados_unidad = query.order_by(UsuarioGlobal.nombre_completo).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('panel_encargado_recinto.html',
                           pagination=encargados_unidad,
                           busqueda=busqueda)