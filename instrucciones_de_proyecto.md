# Guía de Inicio de Proyecto: Sistema Mesa de Ayuda (Django + OpenCode)

Este documento contiene la arquitectura, modelos, requerimientos e instrucciones paso a paso para la inicialización y desarrollo del sistema de gestión de tickets de Mesa de Ayuda utilizando **Django**.

---

## 1. Resumen de Requerimientos y Especificaciones

### Requisitos Funcionales (RF)
- **RF01:** Autenticación de usuarios mediante correo/usuario y contraseña.
- **RF02:** Registro de tickets por clientes (Título, Descripción, Categoría/Prioridad).
- **RF03:** Asignación de tickets a agentes por el administrador.
- **RF04:** Vista de tickets asignados para el agente.
- **RF05:** Actualización de estados (*Nuevo*, *En Proceso*, *Resuelto*, *Cerrado*) y adición de comentarios.
- **RF06:** Cierre del ticket detallando la resolución del problema.
- **RF07:** Panel de administración para gestión de usuarios (Cliente, Agente, Admin).

### Requisitos No Funcionales (RNF)
- **RNF01 (Plataforma):** Aplicación web accesible y responsiva.
- **RNF02 (Seguridad):** Contraseñas encriptadas en DB (uso del Custom User Model de Django).
- **RNF03 (Usabilidad):** UI limpia de pocos pasos para registrar o actualizar tickets.

---

## 2. Modelo de Base de Datos (Django ORM)

### Estrategia de Modelado
1. **`Usuario` (Extiende `AbstractUser`)**:
   - `rol`: ChoiceField (`cliente`, `agente`, `admin`).
   - `email`: Unique Field.

2. **`Ticket`**:
   - `titulo`: CharField(max_length=200)
   - `descripcion`: TextField
   - `prioridad`: ChoiceField (`Baja`, `Media`, `Alta`)
   - `estado`: ChoiceField (`Nuevo`, `Asignado`, `En Proceso`, `Resuelto`, `Cerrado`)
   - `cliente`: ForeignKey a `Usuario` (related_name='tickets_creados')
   - `agente`: ForeignKey a `Usuario` (related_name='tickets_asignados', null=True, blank=True)
   - `fecha_creacion`: DateTimeField(auto_now_add=True)
   - `fecha_cierre`: DateTimeField(null=True, blank=True)

3. **`Seguimiento`**:
   - `ticket`: ForeignKey a `Ticket` (related_name='seguimientos')
   - `usuario`: ForeignKey a `Usuario`
   - `comentario`: TextField
   - `fecha`: DateTimeField(auto_now_add=True)

---

## 3. Instrucciones Paso a Paso para OpenCode

### Paso 1: Configuración del Entorno de Desarrollo

Ejecuta en la terminal los siguientes comandos:

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# 3. Instalar dependencias
pip install django pillow
```

---

### Paso 2: Inicialización del Proyecto Django

```bash
# Crear el proyecto
django-admin startproject mesa_ayuda .

# Crear la aplicación principal
python manage.py startapp tickets
```

---

### Paso 3: Configuración del Modelo de Usuario Personalizado

En `mesa_ayuda/settings.py`, agrega la app y define el modelo de usuario personalizado:

```python
INSTALLED_APPS = [
    # ...
    'tickets',
]

# Especificar modelo de usuario personalizado
AUTH_USER_MODEL = 'tickets.Usuario'
```

En `tickets/models.py`:

```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = (
        ('cliente', 'Cliente'),
        ('agente', 'Agente'),
        ('admin', 'Administrador'),
    )
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"


class Ticket(models.Model):
    PRIORIDADES = (
        ('Baja', 'Baja'),
        ('Media', 'Media'),
        ('Alta', 'Alta'),
    )
    ESTADOS = (
        ('Nuevo', 'Nuevo'),
        ('Asignado', 'Asignado'),
        ('En Proceso', 'En Proceso'),
        ('Resuelto', 'Resuelto'),
        ('Cerrado', 'Cerrado'),
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='Media')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Nuevo')
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tickets_creados')
    agente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_asignados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TKT-{self.id:03d} - {self.titulo}"


class Seguimiento(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='seguimientos')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario por {self.usuario.username} en TKT-{self.ticket.id}"
```

---

### Paso 4: Migraciones y Creación del Superusuario

```bash
# Crear y aplicar migraciones iniciales
python manage.py makemigrations
python manage.py migrate

# Crear superusuario para el Admin Dashboard
python manage.py createsuperuser
```

---

### Paso 5: Configuración del Panel de Administración (`admin.py`)

En `tickets/admin.py`:

```python
from django.contrib import admin
from .models import Usuario, Ticket, Seguimiento

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'rol', 'is_staff')
    list_filter = ('rol',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'cliente', 'agente', 'prioridad', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'prioridad')
    search_fields = ('titulo', 'descripcion')

@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'usuario', 'fecha')
```

---

### Paso 6: Vistas Principales (Dashboard & Detalle de Ticket)

En `tickets/views.py`:

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Ticket, Seguimiento
from django.utils import timezone

@login_required
def dashboard_view(request):
    user = request.user
    if user.rol == 'admin':
        tickets = Ticket.objects.all().order_by('-fecha_creacion')
        unassigned = Ticket.objects.filter(agente__isnull=True)
        context = {
            'total': tickets.count(),
            'nuevos': tickets.filter(estado='Nuevo').count(),
            'en_proceso': tickets.filter(estado='En Proceso').count(),
            'cerrados': tickets.filter(estado='Cerrado').count(),
            'recientes': tickets[:5],
            'sin_asignar': unassigned,
        }
        return render(request, 'dashboard_admin.html', context)
    
    elif user.rol == 'agente':
        tickets = Ticket.objects.filter(agente=user).order_by('-fecha_creacion')
        context = {
            'nuevos': tickets.filter(estado='Nuevo').count(),
            'en_proceso': tickets.filter(estado='En Proceso').count(),
            'resueltos': tickets.filter(estado='Resuelto').count(),
            'tickets': tickets
        }
        return render(request, 'dashboard_agente.html', context)
    
    else: # Cliente
        tickets = Ticket.objects.filter(cliente=user).order_by('-fecha_creacion')
        return render(request, 'dashboard_cliente.html', {'tickets': tickets})


@login_required
def detalle_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    
    if request.method == 'POST':
        # Agregar comentario o cambiar estado
        comentario = request.POST.get('comentario')
        nuevo_estado = request.POST.get('estado')
        
        if comentario:
            Seguimiento.objects.create(
                ticket=ticket,
                usuario=request.user,
                comentario=comentario
            )
        if nuevo_estado:
            ticket.estado = nuevo_estado
            if nuevo_estado == 'Cerrado':
                ticket.fecha_cierre = timezone.now()
            ticket.save()
            
        return redirect('detalle_ticket', ticket_id=ticket.id)

    return render(request, 'detalle_ticket.html', {'ticket': ticket})
```

---

### Paso 7: Estructura de Plantillas Recomendada

Diseñar plantillas con **Tailwind CSS** o **Bootstrap 5** respetando la paleta de colores del prototipo (Figma):
- **Barra lateral oscura**: `#1e1e2d`
- **Badges de estado**:
  - *Nuevo / Azul*: `#3b82f6`
  - *En Proceso / Amarillo*: `#f59e0b`
  - *Resuelto / Verde*: `#10b981`
  - *Cerrado / Gris*: `#6b7280`
```
tickets/
└── templates/
    ├── base.html
    ├── dashboard_admin.html
    ├── dashboard_agente.html
    ├── dashboard_cliente.html
    └── detalle_ticket.html
```

---

## 4. Comandos para Ejecución

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver
```

Acceder a `http://127.0.0.1:8000/admin/` para crear los roles iniciales y verificar el funcionamiento.