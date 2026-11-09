# Credenciales de Usuarios de Prueba — Fixpoint

> Generados con `python manage.py seed_demo`.
> **Solo para desarrollo.** Cambia o elimina estas cuentas antes de cualquier uso real.

## Usuarios

| Rol | Nombre | Correo | Usuario | Contraseña |
|---|---|---|---|---|
| Administrador | Admin Principal | `admin@mesa.test` | `admin` | `admin12345` |
| Agente | Ana Agente | `agente1@mesa.test` | `agente1` | `agente12345` |
| Agente | Bruno Soporte | `agente2@mesa.test` | `agente2` | `agente12345` |
| Cliente | Carla Cliente | `cliente1@mesa.test` | `cliente1` | `cliente12345` |
| Cliente | Diego Cliente | `cliente2@mesa.test` | `cliente2` | `cliente12345` |
| Cliente | Elena Cliente | `cliente3@mesa.test` | `cliente3` | `cliente12345` |

> El inicio de sesión se hace con **correo electrónico** (no con el nombre de usuario).

## Qué puede hacer cada rol

| Acción | Cliente | Agente | Administrador |
|---|---|---|---|
| Crear ticket | ✅ | ❌ | ❌ |
| Ver tickets | Solo los propios | Solo los asignados | Todos |
| Comentar | ✅ (propios) | ✅ (asignados) | ✅ (todos) |
| Cambiar estado | ❌ | ✅ (asignados) | ✅ |
| Cerrar con resolución | ❌ | ✅ (asignados) | ✅ |
| Asignar agente | ❌ | ❌ | ✅ |
| Recibir notificaciones internas (campana) | ✅ | ✅ | ✅ |
| Gestionar usuarios (`/admin/`) | ❌ | ❌ | ✅ |

## Regenerar los datos

```bash
python manage.py seed_demo
```

El comando es idempotente: si los usuarios existen, actualiza su contraseña y rol;
si ya hay tickets, no genera tickets nuevos.

## Crear un administrador adicional

```bash
python manage.py createsuperuser
```
