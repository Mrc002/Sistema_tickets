# Fixpoint — Gestión de Soporte Técnico

Aplicación web centralizada para la recepción y seguimiento de solicitudes de soporte técnico, construida con Django y Bootstrap 5.

> **Fuente de verdad:** `especificaci_n_del_proyecto.md`.
> El estado de implementación se detalla en `REQUERIMIENTOS.md`.

## Alcance

- **Clientes:** crean incidencias (título, descripción y prioridad) y consultan su estado.
- **Agentes:** atienden únicamente los tickets asignados, actualizan estados, comentan y cierran con resolución.
- **Administradores:** gestionan usuarios, asignan agentes y tienen acceso global a los tickets.
- **Notificaciones:** 100 % internas mediante campana dentro de la aplicación. **No se envían correos automáticos** (fuera de alcance).

## Requisitos

- Python 3.11+
- Dependencias de `requirements.txt` (Django 6.1.2, Pillow)
- SQLite3 (incluido con Python)

## Puesta en marcha

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. (Opcional) Crear superusuario
python manage.py createsuperuser

# 5. (Opcional) Cargar datos de ejemplo
python manage.py seed_demo

# 6. Ejecutar el servidor
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

## Credenciales de ejemplo (`seed_demo`)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@mesa.test` | `admin12345` |
| Agente | `agente1@mesa.test` | `agente12345` |
| Agente | `agente2@mesa.test` | `agente12345` |
| Cliente | `cliente1@mesa.test` | `cliente12345` |
| Cliente | `cliente2@mesa.test` | `cliente12345` |
| Cliente | `cliente3@mesa.test` | `cliente12345` |

> Cambia estas credenciales antes de cualquier uso real.

## Roles y permisos

| Acción | Cliente | Agente | Admin |
|---|---|---|---|
| Crear ticket | ✅ | ❌ | ❌ |
| Ver tickets | ✅ (propios) | ✅ (asignados) | ✅ (todos) |
| Editar / cancelar ticket | ✅ (propio y `Nuevo`) | ❌ | ❌ |
| Comentar (público e interno) | ✅ (propios) | ✅ (asignados) | ✅ (todos) |
| Cambiar estado y prioridad | ❌ | ✅ (asignados) | ✅ |
| Cerrar con resolución | ❌ | ✅ (asignados) | ✅ |
| Reabrir ticket cerrado | ❌ | ❌ | ✅ |
| Asignar agente | ❌ | ❌ | ✅ |
| Exportar CSV | ❌ | ❌ | ✅ |
| Gestionar usuarios | ❌ | ❌ | ✅ (`/admin/`) |

## Funcionalidades

- Login por email, registro público de clientes y cierre de sesión.
- Perfil editable (nombre y apellido) y cambio de contraseña.
- Tickets con título, descripción, categoría y prioridad; código `TKT-XXX`.
- Máquina de estados validada: `Nuevo → Asignado → En Proceso → Resuelto → Cerrado`, más `Cancelado`.
- Cierre con resolución obligatoria (mínimo 10 caracteres) y reapertura por el admin con motivo.
- Comentarios de seguimiento con historial automático de cambios (estado, prioridad, asignación).
- Comentarios internos visibles solo para agentes y administradores.
- Asignación y reasignación de agentes; liberación automática de tickets al desactivar/eliminar un agente.
- **Campana de notificaciones internas** con contador de no leídas, bandeja paginada y marca de leídas.
- SLA por prioridad (Alta 4 h, Media 24 h, Baja 72 h) con marca de vencimiento.
- Filtros por texto, estado, prioridad, agente y rango de fechas; paginación de 20.
- Exportación CSV del listado filtrado (solo admin).
- Tickets `Cerrado`/`Cancelado` de solo lectura, salvo reapertura del admin.

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/` | Dashboard según rol |
| `/login/`, `/registro/`, `/logout/` | Autenticación |
| `/notificaciones/` | Bandeja de notificaciones internas |
| `/notificaciones/<id>/abrir/` | Abrir notificación y marcarla como leída |
| `/perfil/`, `/perfil/password/` | Perfil y cambio de contraseña |
| `/tickets/nuevo/` | Crear ticket (cliente) |
| `/tickets/<id>/` | Detalle y acciones del ticket |
| `/tickets/<id>/editar/` | Editar ticket propio en estado `Nuevo` |
| `/tickets/<id>/asignar/` | Asignar agente (admin) |
| `/tickets/exportar/` | Exportar CSV (admin) |
| `/admin/` | Gestión de usuarios y datos |

## Estructura

```
mesa_ayuda/            # configuración del proyecto
tickets/
  models.py            # Usuario, Ticket, Seguimiento y Notificacion
  forms.py             # formularios, filtros y validaciones
  views.py             # dashboards, detalle, notificaciones, CSV, perfil
  services.py          # auditoría, notificaciones internas y asignación
  context_processors.py# contador y resumen de la campana
  urls.py              # rutas de la app
  admin.py             # panel de administración y protecciones
  decorators.py        # control de acceso por rol y por objeto
  management/commands/seed_demo.py
  tests.py             # 40 pruebas de permisos, flujos y notificaciones
templates/             # plantillas (Bootstrap 5)
```

## Pruebas

```bash
python manage.py test
```

## Requerimientos cubiertos

Requerimientos de la especificación (`especificaci_n_del_proyecto.md`):

- **RF-01, RF-02, RF-04** Registro, login por email y cambio de contraseña.
- **RF-07 al RF-11** Gestión de usuarios, roles, activación, contraseñas y protección del admin.
- **RF-12** Liberación de tickets al desactivar un agente.
- **RF-13, RF-18** Creación, edición y cancelación de tickets.
- **RF-21** Asignación y reasignación de agentes.
- **RF-23** Comentarios cronológicos públicos e internos.
- **RF-27, RF-28** Máquina de estados y cierre con resolución.
- **RN-01 a RN-10 y RN-15** Reglas transversales de identidad, aislamiento, estados e inmutabilidad.
- **Notificaciones internas** (campana) en lugar de correos automáticos.

Mejoras adicionales que no contradicen la especificación: categorías, SLA, filtros, paginación, exportación CSV, historial automático de cambios, perfil y reapertura. Ver `REQUERIMIENTOS.md`.

## Variables de entorno (opcional)

Copia `.env.example` a `.env` y ajusta:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
