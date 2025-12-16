# 📘 Sistema Libro de Novedades - Salud MAHO

Aplicación web desarrollada para la **Unidad de TICs del Departamento de Salud de la Municipalidad de Alto Hospicio**. Este sistema digitaliza el proceso de "Hoja de Vida" de los funcionarios, reemplazando el registro en papel por una gestión centralizada, segura y transparente de las anotaciones de mérito y demérito.

## 🚀 Características Principales

* **Digitalización de Procesos:** Registro histórico de eventos (felicitaciones, amonestaciones, observaciones) categorizados por Factores y Subfactores.
* **Flujo de Notificaciones:** Envío automático de correos electrónicos al funcionario cuando se crea una nueva anotación.
* **Gestión de Jerarquías Compleja:**
    * **Doble Jefatura:** Soporte para asignar un "Jefe Directo" y un "Segundo Jefe" simultáneos, permitiendo que ambos gestionen al mismo funcionario.
    * **Perfiles de Rol:** Admin, Jefa de Salud, Encargado de Recinto, Encargado de Unidad y Funcionario.
* **Toma de Conocimiento:** Flujo digital donde el funcionario debe ingresar al sistema para leer y marcar *“Tomo Conocimiento”* de sus anotaciones, con opción de agregar comentario u observación.
* **Reportabilidad:**
    * **Generación de PDF:** Exportación de la Hoja de Vida completa con diseño institucional y nota legal al pie (Librería `FPDF2`).
    * Filtros avanzados por fecha, tipo de anotación y factor.
* **Seguridad y Auditoría:**
    * Protección CSRF en todos los formularios.
    * Registro detallado de Logs (Inicios de sesión, creación de comentarios, cambios de contraseñas).
    * Validación de contraseñas seguras.
    * Forzado de cambio de contraseña en primer inicio.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, Flask.
* **Base de Datos:** MySQL (SQLAlchemy ORM).
* **Frontend:** HTML5, Jinja2, TailwindCSS (CDN), JavaScript.
* **Librerías Clave:**
    * `FPDF2`: Generación de reportes PDF compatibles con Unicode.
    * `Flask-Login`: Gestión de sesiones.
    * `Flask-Mail`: Envío de notificaciones SMTP.
    * `pytz`: Gestión de Zona Horaria (America/Santiago).

## 📂 Estructura del Proyecto

El proyecto sigue una arquitectura modular basada en **Blueprints**:

```text
libro_de_novedades/
├── blueprints/          # Lógica modular (Admin, Auth, Libro, Jefa, Unidad, Recinto)
├── static/              # Assets (Logos institucionales, JS, CSS)
├── templates/           # Vistas HTML (Jinja2) con herencia de base.html
├── utils/               # Módulo de utilidades refactorizado
│   ├── __init__.py      # Exportación de funciones
│   ├── decorators.py    # Decoradores de roles (admin_required, jefa_required, etc.)
│   └── helpers.py       # Lógica auxiliar (Correos, Logs, Jerarquía, PDF)
├── app.py               # Inicialización de la aplicación
├── models.py            # Modelos de Base de Datos (Usuario, Comentario, Factor, etc.)
├── extensions.py        # Instancias de extensiones (login_manager, csrf)
└── requirements.txt     # Dependencias del proyecto
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
SECRET_KEY=tu_clave_secreta
MYSQL_PASSWORD=tu_password_mysql
EMAIL_USUARIO=tu_correo@gmail.com
EMAIL_CONTRASENA=tu_contraseña_aplicacion
```
5. Ejecutar:

```bash
python app.py
```
---
Desarrollado por **Josting Silva**  
Analista Programador – Unidad de TICs  
Departamento de Salud, Municipalidad de Alto Hospicio
