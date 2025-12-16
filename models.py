# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

# Creamos la instancia de SQLAlchemy aquí. 
# La conectaremos a la aplicación en app.py para evitar importaciones circulares.
db = SQLAlchemy()

# --- 2. FUNCIÓN AYUDANTE PARA HORA CHILE ---
# NOTA IMPORTANTE:
# Este sistema usa la hora local de Chile con pytz.
# Si deseas utilizar UTC (recomendado para sistemas globales),
# reemplaza obtener_hora_chile() por datetime.utcnow
# y ajusta las funciones de timestamp en auth.py y libro.py.
def obtener_hora_chile():
    chile_tz = pytz.timezone('America/Santiago')
    return datetime.now(chile_tz).replace(tzinfo=None)

# --- MODELO GLOBAL (Fuente de la Verdad) ---
class UsuarioGlobal(db.Model):
    __tablename__ = 'usuarios_global'
    __table_args__ = {'schema': 'mahosalu_usuarios_global'} 

    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(12))
    nombre_completo = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    activo = db.Column(db.Boolean)
    
    # Datos RRHH (Relaciones Globales)
    unidad_id = db.Column(db.Integer) # Asumimos IDs por simplicidad cruzada
    establecimiento_id = db.Column(db.Integer)
    calidad_juridica_id = db.Column(db.Integer)
    categoria_id = db.Column(db.Integer)
    
    # Para poder acceder a los nombres (necesitas definir los modelos de catálogo global también
    # o hacer joins manuales. Por ahora, asumimos que usas los IDs o cargas los objetos).
    # Si quieres usar los nombres de Unidad/Establecimiento, necesitas mapear esas tablas globales también
    # o mantenerlas locales solo como catálogo de consulta.
    
    cambio_clave_requerido = db.Column(db.Boolean)
    reset_token = db.Column(db.String(32))
    reset_token_expiracion = db.Column(db.DateTime)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# --- MODELOS DE CATÁLOGO LOCALES (Solo lectura para los selects) ---
class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    usuarios = db.relationship('Usuario', back_populates='rol')

class Establecimiento(db.Model):
    __tablename__ = 'establecimientos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

class Unidad(db.Model):
    __tablename__ = 'unidades'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False) 
    establecimiento_id = db.Column(db.Integer, db.ForeignKey('establecimientos.id'), nullable=False)

class CalidadJuridica(db.Model):
    __tablename__ = 'calidadesjuridicas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(1), unique=True, nullable=False)

class Factor(db.Model):
    __tablename__ = 'factores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    subfactores = db.relationship('SubFactor', back_populates='factor')

class SubFactor(db.Model):
    __tablename__ = 'subfactores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    factor_id = db.Column(db.Integer, db.ForeignKey('factores.id'))
    factor = db.relationship('Factor', back_populates='subfactores')
    comentarios = db.relationship('Comentario', back_populates='subfactor')

# --- USUARIO LOCAL (Limpio) ---
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=obtener_hora_chile)
    
    # Vínculo Global
    usuario_global_id = db.Column(db.Integer, nullable=False, unique=True)
    
    identidad = db.relationship('UsuarioGlobal', 
                                primaryjoin='Usuario.usuario_global_id == UsuarioGlobal.id',
                                foreign_keys='Usuario.usuario_global_id',
                                uselist=False, viewonly=True)

    # --- PROXIES DE IDENTIDAD (Datos Personales) ---
    @property
    def nombre_completo(self):
        return self.identidad.nombre_completo if self.identidad else "Desconocido"
    
    @property
    def rut(self):
        return self.identidad.rut if self.identidad else "S/R"

    @property
    def email(self):
        return self.identidad.email if self.identidad else ""
    
    @property
    def cambio_clave_requerido(self):
        return self.identidad.cambio_clave_requerido if self.identidad else False

    # --- PROXIES DE CONTRATO (Redirigimos al global) ---
    # Esto simula que el usuario local tiene unidad, pero la lee del global
    @property
    def unidad(self):
        if self.identidad and self.identidad.unidad_id:
            return Unidad.query.get(self.identidad.unidad_id)
        return None
    
    @property
    def establecimiento(self):
        if self.identidad and self.identidad.establecimiento_id:
            return Establecimiento.query.get(self.identidad.establecimiento_id)
        return None

    @property
    def calidad_juridica(self):
        if self.identidad and self.identidad.calidad_juridica_id:
            return CalidadJuridica.query.get(self.identidad.calidad_juridica_id)
        return None
        
    @property
    def categoria(self):
        if self.identidad and self.identidad.categoria_id:
            return Categoria.query.get(self.identidad.categoria_id)
        return None

    # --- DATOS LOCALES REALES (Solo lo que administramos aquí) ---
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    rol = db.relationship('Rol', back_populates='usuarios')

    jefe_directo_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    segundo_jefe_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    subordinados = db.relationship('Usuario',
                                  backref=db.backref('jefe_directo', remote_side=[id]),
                                  lazy='dynamic',
                                  foreign_keys=[jefe_directo_id])

    segundo_jefe = db.relationship('Usuario', 
                                   remote_side=[id],
                                   foreign_keys=[segundo_jefe_id],
                                   backref='subordinados_secundarios')

    # Métodos legacy para evitar crashes
    def check_password(self, password):
        return self.identidad.check_password(password) if self.identidad else False

class Comentario(db.Model):
    __tablename__ = 'comentarios'
    folio = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('Favorable', 'Desfavorable'), nullable=False)
    motivo_jefe = db.Column(db.Text, nullable=False)
    observacion_funcionario = db.Column(db.Text)
    estado = db.Column(db.Enum('Pendiente', 'Aceptada'), default='Pendiente')
    fecha_creacion = db.Column(db.Date, nullable=False)
    fecha_aceptacion = db.Column(db.DateTime)
    
    funcionario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    jefe_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    subfactor_id = db.Column(db.Integer, db.ForeignKey('subfactores.id'), nullable=False)

    subfactor = db.relationship('SubFactor', back_populates='comentarios')
    funcionario = db.relationship('Usuario', foreign_keys=[funcionario_id], backref='comentarios_recibidos')
    jefe = db.relationship('Usuario', foreign_keys=[jefe_id], backref='comentarios_emitidos')

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=obtener_hora_chile) 
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_nombre = db.Column(db.String(255))
    accion = db.Column(db.String(255), nullable=False)
    detalles = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref=db.backref('logs', lazy=True), foreign_keys=[usuario_id])