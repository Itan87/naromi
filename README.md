# Sistema de Gestión de Inventario Industrial - Naromi Studio

Práctica Profesional 4 
Sistema desarrollado en Django que implementa un sistema de gestión de inventario industrial, incluyendo gestión de usuarios, inventario de productos y pedidos.

## Características

- **Gestión de Usuarios**: Sistema de autenticación con roles (Administrador y Empleado)
- **Inventario de Productos**: Control de stock con alertas de stock mínimo
- **Gestión de Pedidos**: Seguimiento de pedidos desde ingreso hasta completado
- **Interfaz Administrativa**: Panel de administración de Django con funcionalidades personalizadas
- **Formularios con Bootstrap 5**: Interfaz moderna usando django-crispy-forms

## Requisitos del Sistema

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd naromi
```

### 2. Crear un Entorno Virtual (Recomendado)

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la Base de Datos

```bash
# Aplicar migraciones
python manage.py migrate

# Crear un superusuario (opcional)
python manage.py createsuperuser
```

### 5. Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000/`

## Uso del Sistema

### Acceso Principal

- **Página Principal**: `http://127.0.0.1:8000/`
- **Panel de Administración**: `http://127.0.0.1:8000/admin/`

### Funcionalidades Disponibles

#### 1. Gestión de Usuarios
- Crear usuarios con roles específicos (Administrador/Empleado)
- Autenticación y autorización
- Panel de administración personalizado

#### 2. Gestión de Productos
- Crear y editar productos con SKU único
- Control de stock actual y mínimo
- Alertas automáticas cuando el stock está por debajo del mínimo
- Búsqueda y filtrado por color, talla, etc.

#### 3. Gestión de Pedidos
- Crear pedidos con información del cliente
- Seguimiento de estados: Ingresado → Presupuestado → Aprobado → Orden de Trabajo → Completado
- Gestión de insumos por pedido
- Validación automática de stock al cambiar a "Orden de Trabajo"

### Estados de Pedidos

1. **Ingresado**: Pedido recién creado
2. **Presupuestado**: Presupuesto generado
3. **Aprobado**: Pedido aprobado por el cliente
4. **Orden de Trabajo**: En proceso de producción
5. **Completado**: Pedido finalizado
6. **Cancelado**: Pedido cancelado

## Estructura del Proyecto

```
naromi/
├── gestion/                 # Configuración principal de Django
│   ├── __init__.py
│   ├── settings.py         # Configuración del proyecto
│   ├── urls.py            # URLs principales
│   ├── wsgi.py            # Configuración WSGI
│   └── asgi.py            # Configuración ASGI
├── gestion_general/        # Aplicación principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas
│   ├── admin.py           # Configuración del admin
│   ├── migrations/        # Migraciones de base de datos
│   └── tests.py           # Tests unitarios
├── manage.py              # Script de gestión de Django
├── requirements.txt       # Dependencias del proyecto
└── README.md             # Este archivo
```

## Modelos de Datos

### Usuario
- Extiende el modelo de usuario de Django
- Roles: Administrador y Empleado
- Campos adicionales para gestión de roles

### Producto
- SKU único para identificación
- Información básica (nombre, descripción, color, talla)
- Control de stock (actual y mínimo)
- Precio unitario

### Pedido
- Información del cliente
- Estado del pedido
- Usuario que creó el pedido
- Total del pedido

### PedidoInsumo
- Relación entre pedidos y productos
- Cantidad requerida por producto

## Tecnologías Utilizadas

- **Django 5.2.6**: Framework web principal
- **SQLite**: Base de datos (desarrollo)
- **django-crispy-forms**: Formularios con Bootstrap 5
- **Gunicorn**: Servidor WSGI para producción
- **WhiteNoise**: Servir archivos estáticos

## Comandos Útiles

```bash
# Crear migraciones después de cambios en modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Configurar permisos de usuarios
python manage.py setup_permissions

# Ejecutar tests
python manage.py test

# Recopilar archivos estáticos (producción)
python manage.py collectstatic
```

## Desarrollo

### Agregar Nuevas Funcionalidades

1. Modificar modelos en `gestion_general/models.py`
2. Crear migraciones: `python manage.py makemigrations`
3. Aplicar migraciones: `python manage.py migrate`
4. Actualizar vistas en `gestion_general/views.py`
5. Configurar URLs en `gestion/urls.py`

### Personalizar el Admin

Las configuraciones del panel de administración se encuentran en `gestion_general/admin.py` y incluyen:
- Personalización de listas de visualización
- Filtros y búsquedas
- Validaciones personalizadas
- Inlines para relaciones

## Solución de Problemas

## Datos de Prueba

### Cargar Datos de Prueba
Para cargar datos de prueba en la base de datos, ejecutar:
```bash
python manage.py load_mock_data
```

Este comando creará:
1. Usuarios de prueba:
   - Administrador:
     - Email/Usuario: admin@taller.com
     - Contraseña: admin123
     - Rol: Administrador
   - Encargado:
     - Email/Usuario: encargado@taller.com
     - Contraseña: encargado123
     - Rol: Empleado
2. 20 productos de ropa
3. 10 pedidos de ejemplo con estados aleatorios

### Error de Base de Datos
```bash
# Si hay problemas con migraciones
python manage.py migrate --run-syncdb
```

### Error de Dependencias
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Puerto en Uso
```bash
# Usar un puerto diferente
python manage.py runserver 8001
```
