# 📘 Sistema Libro de Novedades - Salud MAHO

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)
![Database](https://img.shields.io/badge/Database-MySQL-blue.svg)
![ORM](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)

Aplicación web desarrollada para la **Unidad de TICs del Departamento de Salud de la Municipalidad de Alto Hospicio**. Este sistema digitaliza el proceso de "Hoja de Vida" de los funcionarios, reemplazando el registro en papel por una gestión centralizada, segura y transparente de las anotaciones de mérito y demérito.

## 🚀 Características Principales

* **Digitalización de Procesos:** Registro histórico de eventos (felicitaciones, amonestaciones, observaciones) categorizados por Factores y Subfactores.
* **Flujo de Notificaciones:** Envío automático de correos electrónicos al funcionario cuando se crea una nueva anotación, con plantillas institucionales unificadas.
* **Gestión de Jerarquías Compleja:**
    * **Doble Jefatura:** Soporte para asignar un "Jefe Directo" y un "Segundo Jefe" simultáneos, permitiendo que ambos gestionen al mismo funcionario.
    * **Perfiles de Rol:** Admin, Jefa de Salud, Encargado de Recinto, Encargado de Unidad y Funcionario.
* **Toma de Conocimiento:** Flujo digital donde el funcionario debe ingresar al sistema para leer y marcar *“Tomo Conocimiento”* de sus anotaciones, con opción de agregar comentario u observación.
* **Reportabilidad:**
    * **Generación de PDF:** Exportación de la Hoja de Vida completa generada dinámicamente en el back-end con diseño institucional y nota legal al pie (Librería `fpdf2`).
    * Filtros avanzados por fecha, tipo de anotación y factor en todas las vistas.
* **Seguridad, Auditoría y UX:**
    * Protección CSRF y prevención de doble envío en todos los formularios.
    * Registro detallado de Logs (Inicios de sesión, creación de comentarios, cambios de estado).
    * Cierre de sesión dinámico automático por inactividad del usuario.
    * Validación estricta de contraseñas seguras y forzado de cambio en el primer inicio.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Flask (Patrón Application Factory).
* **Base de Datos:** MySQL (SQLAlchemy ORM).
* **Frontend:** HTML5, Jinja2, TailwindCSS (CDN), JavaScript Vanilla.
* **Librerías Clave:**
    * `fpdf2`: Generación de reportes PDF programáticos compatibles con Unicode.
    * `Flask-Login`: Gestión avanzada de sesiones.
    * `smtplib` / `email.mime`: Motor nativo para envío de notificaciones seguras.
    * `pytz`: Gestión de Zona Horaria estricta (`America/Santiago`).
    * `waitress`: Servidor WSGI para despliegue en producción.

## 📂 Estructura del Proyecto

El proyecto sigue una arquitectura modular y estandarizada basada en **Blueprints**:

```text
libro_de_novedades/
├── blueprints/          # Lógica modular (admin, auth, libro, jefa_salud, recinto, unidad)
├── static/              # Assets estáticos
│   ├── css/             # Hojas de estilo
│   ├── img/             # Logos institucionales e iconos
│   └── js/              # Scripts (validaciones, modales, filtros, timeout)
├── templates/           # Vistas HTML (Jinja2) con herencia de base.html y macros
│   ├── admin/           # Vistas del panel de administración y logs
│   ├── auth/            # Vistas de inicio de sesión y recuperación de claves
│   ├── errors/          # Páginas de error personalizadas (403, 404, 500)
│   ├── jefatura/        # Vistas de paneles para los roles de jefatura
│   └── libro/           # Vistas principales del libro de novedades y comentarios
├── utils/               # Módulo genérico de utilidades
│   ├── __init__.py      # Exportación de funciones
│   ├── decorators.py    # Control de acceso por roles y estado de contraseñas
│   ├── email.py         # Motor de plantillas HTML y envío de correos
│   └── helpers.py       # Lógica auxiliar (Cálculo de jerarquía, Logs del sistema)
├── app.py               # Archivo principal (Application Factory e inicialización)
├── extensions.py        # Instancias desacopladas (Flask-Login, CSRFProtect)
├── models.py            # Modelos SQLAlchemy (Usuario, Comentario, Factor, Log)
└── requirements.txt     # Dependencias optimizadas del proyecto
```
## 🌿 Gestión de Ramas y Despliegue
Este repositorio maneja dos flujos de trabajo distintos para separar el desarrollo local de la producción con identidad centralizada:

1. **Rama `main`** (Desarrollo Local / Standalone)
* **Autenticación:** Local (Tabla usuarios interna).

* **Uso:** Para desarrollo, pruebas de nuevas funcionalidades y uso offline.

* **Base de Datos:** Esquema local hoja_de_vida_db.

2. **Rama `produccion-global`** (Despliegue)
* **Autenticación:** Centralizada (Identidad Global).

* **Arquitectura**
    * El modelo `Usuario` local ya no guarda credenciales.
    * Se conecta a una Base de Datos externa mediante proxies en SQL.
    * Valida credenciales contra la tabla maestra y autoriza permisos según la tabla local.

* **Uso:** Versión productiva desplegada en el Hosting/CPanel.

## ⚙️ Instalación Local

1. Clonar el repositorio:

```bash
git clone https://github.com/Yosh457/libro-de-novedades.git
cd libro-de-novedades
```
2. Crear entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```
3. Instalar dependencias:

```bash
pip install -r requirements.txt
```
4. Configurar variables de entorno (.env):

```env
SECRET_KEY="tu_clave_secreta_aqui"
MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASSWORD="tu_password_mysql"
MYSQL_DB="hoja_de_vida_db"

EMAIL_USUARIO="unidad.tics@mahosalud.cl"
EMAIL_CONTRASENA="tu_contraseña_aplicacion"
```
5. Inicializar la base de datos y ejecutar el servidor de desarrollo:

```bash
python app.py
```
---
Desarrollado por **Josting Silva**  
Analista Programador – Unidad de TICs  
Departamento de Salud, Municipalidad de Alto Hospicio
