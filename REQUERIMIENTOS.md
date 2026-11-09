# Requerimientos del Sistema — Fixpoint

> **Fuente de verdad:** `especificaci_n_del_proyecto.md`.
> Este documento resume esa especificación y añade el **estado de implementación** del proyecto.
> Si hay alguna discrepancia, prevalece `especificaci_n_del_proyecto.md`.

---

## 1. Contexto y alcance

**Organización:** PyME de comercialización y mantenimiento de equipos TI.

**Problema:** falta de un canal único para recibir y dar seguimiento a las solicitudes de soporte técnico.

**Solución (Fixpoint):** aplicación web centralizada en Django que conecta las necesidades de los usuarios con el servicio técnico de forma organizada y transparente.

### Incluido

- Registro de incidencias (título, descripción, prioridad) y consulta de estado para **Clientes**.
- Panel de administración de usuarios y asignación formal de tickets para **Administradores**.
- Tablero de tickets asignados, actualización de estados, comentarios internos/públicos y cierre con resolución para **Agentes**.
- Notificaciones **100 % internas** dentro del sistema (campana).

### Excluido

- Aplicaciones móviles nativas.
- Integración con APIs externas (WhatsApp, SMS, correos electrónicos automatizados).
- Pasarelas de pago y control de inventario físico.

> **Decisión de diseño:** no se envían correos automáticos. Toda notificación se muestra en la campana interna del sistema.

---

## 2. Roles del sistema

| Rol | Descripción | Permisos básicos |
|---|---|---|
| **Visitante** | Usuario sin sesión activa. | Solo puede registrarse e iniciar sesión. Al registrarse se le asigna el rol `cliente`. |
| **Cliente** | Usuario final que reporta fallas. | Crea tickets y da seguimiento exclusivo a los suyos. |
| **Agente** | Técnico de soporte. | Atiende **únicamente** los tickets que el Admin le asignó. |
| **Admin** | Administrador del sistema. | Administra usuarios, asigna agentes y tiene acceso global a los tickets. |

> El rol es **excluyente**: un usuario tiene exactamente un rol a la vez.

---

## 3. Reglas de negocio transversales

| ID | Regla | Estado |
|---|---|---|
| **RN-01** | `email` es obligatorio, único y es el identificador de inicio de sesión. | ✅ |
| **RN-02** | `username` es obligatorio y único. | ✅ |
| **RN-03** | La contraseña **nunca** se almacena en texto plano (se usa el hasher de Django). | ✅ |
| **RN-04** | Todo ticket nace con estado `Nuevo` y **sin** agente asignado. | ✅ |
| **RN-05** | El código visible de un ticket es `TKT-` + `id` con 3 dígitos (ej. `TKT-001`). | ✅ |
| **RN-06** | Solo un usuario con rol `agente` puede ser asignado como responsable de un ticket. | ✅ |
| **RN-07** | Un ticket **cerrado** es de solo lectura (sin cambios de estado ni comentarios), salvo reapertura por Admin. | ✅ |
| **RN-08** | El cierre de un ticket exige una `resolucion` no vacía (mínimo 10 caracteres). | ✅ |
| **RN-09** | Aislamiento: un cliente nunca puede acceder a tickets de otro cliente (HTTP 403). | ✅ |
| **RN-10** | Aislamiento: un agente nunca puede acceder a tickets no asignados a él (HTTP 403). | ✅ |
| **RN-15** | Los comentarios de seguimiento son **inmutables** una vez creados. | ✅ |

---

## 4. Requerimientos funcionales

La numeración conserva los identificadores de la especificación; los huecos corresponden a requerimientos no incluidos en la versión vigente.

### Autenticación y cuentas

| ID | Requerimiento | Prioridad | Estado |
|---|---|---|---|
| **RF-01** | **Visitante** puede registrarse y se le asigna el rol `cliente` por defecto. | DEBE | ✅ |
| **RF-02** | **Usuario** inicia sesión de forma segura y es redirigido al dashboard según su rol. | DEBE | ✅ |
| **RF-04** | **Usuario autenticado** puede cambiar su contraseña desde el sistema. | DEBERÍA | ✅ |

### Gestión de usuarios (Admin)

| ID | Requerimiento | Prioridad | Estado |
|---|---|---|---|
| **RF-07 al RF-11** | **Admin** puede crear usuarios, editar roles, activar/desactivar cuentas, restablecer contraseñas y no puede auto-eliminarse. | DEBE | ✅ |
| **RF-12** | Al desactivar un agente, sus tickets abiertos regresan a estado `Nuevo` y sin asignar. | DEBERÍA | ✅ |

### Ciclo de vida del ticket

| ID | Requerimiento | Prioridad | Estado |
|---|---|---|---|
| **RF-13** | **Cliente** crea un ticket con título, descripción y prioridad. | DEBE | ✅ |
| **RF-18** | **Cliente** puede editar o cancelar su ticket **solo** si sigue en estado `Nuevo`. | DEBERÍA | ✅ |
| **RF-21** | **Admin** asigna o reasigna un ticket a un **Agente**. | DEBE | ✅ |
| **RF-23** | Todos los roles involucrados pueden agregar comentarios cronológicos. | DEBE | ✅ |
| **RF-27** | Los cambios de estado se validan estrictamente con la **Máquina de Estados**. | DEBE | ✅ |
| **RF-28** | El cierre del ticket obliga a registrar un texto de resolución. | DEBE | ✅ |

---

## 5. Máquina de estados

El ciclo de vida es estricto. Cualquier transición no listada se rechaza en el backend.

**Flujo normal:** `Nuevo` → `Asignado` → `En Proceso` → `Resuelto` → `Cerrado`.

| Estado actual | Transición permitida | Ejecutado por | Condición |
|---|---|---|---|
| `Nuevo` | `Asignado` | Admin | Al asignar un agente. |
| `Nuevo` | `Cancelado` | Cliente | Cancelación manual por el creador. |
| `Asignado` | `En Proceso` | Agente / Admin | Al iniciar el trabajo. |
| `En Proceso` | `Resuelto` | Agente / Admin | Problema solucionado temporalmente. |
| `Resuelto` | `Cerrado` | Agente / Admin | Confirmación final (requiere resolución). |
| `Resuelto` | `En Proceso` | Agente / Admin | Si la solución inicial falló. |
| `Cerrado` | `En Proceso` | Admin | Reapertura manual justificada. |

---

## 6. Matriz de permisos (RBAC)

| Acción | Cliente | Agente | Admin |
|---|---|:---:|:---:|
| Crear ticket | ✅ | ❌ | ❌ |
| Ver tickets | Solo propios | Solo asignados | Todos |
| Cancelar ticket | Solo estado `Nuevo` | ❌ | ❌ |
| Asignar agente | ❌ | ❌ | ✅ |
| Comentar | Propios | Asignados | Todos |
| Cambiar estado | ❌ | Asignados | Todos |
| Cerrar / resolver | ❌ | Asignados | Todos |
| Gestionar usuarios | ❌ | ❌ | ✅ |

---

## 7. Notificaciones internas (campana)

La especificación exige que **todo el flujo y las notificaciones se mantengan dentro del sistema**. Implementación:

- Campana en el panel lateral con contador de notificaciones no leídas.
- Bandeja `/notificaciones/` con historial paginado y acción «Marcar todas como leídas».
- Cada notificación enlaza al ticket correspondiente y se marca como leída al abrirla.
- Se generan notificaciones internas para:
  - Ticket nuevo → administradores.
  - Asignación o reasignación → agente asignado.
  - Cambio de estado → cliente y agente (sin avisar al actor).
  - Cierre → cliente y agente (sin avisar al actor).
  - Comentario público → la contraparte; comentario interno → el agente asignado.
- **No se envían correos electrónicos** (excluido explícitamente por la especificación).

---

## 8. Funcionalidades adicionales implementadas

No contradicen la especificación y se conservan como mejoras:

- Categoría del ticket (`Hardware`, `Software`, `Red`, `Acceso`, `Otro`).
- SLA por prioridad (Alta 4 h, Media 24 h, Baja 72 h) con marca de vencimiento.
- Filtros por texto, estado, prioridad, agente y fechas; paginación de 20.
- Exportación CSV del listado filtrado (Admin).
- Historial automático de cambios de estado, prioridad y asignación.
- Perfil editable y cambio de contraseña.
- Comentarios internos separados de los públicos.
- Reapertura de tickets cerrados por el Admin con motivo.

---

## 9. Estado de implementación

| Aspecto | Estado |
|---|---|
| Requerimientos de la especificación | ✅ Implementados |
| Notificaciones internas (campana) | ✅ Implementadas |
| Correos automáticos | ❌ Fuera de alcance (no implementados) |
| Pruebas automatizadas | ✅ 40 tests en verde |

**Stack real:** Python 3.12, Django 6.1.2, SQLite3, Bootstrap 5, HTML/CSS/JS vanilla.
La especificación menciona Django 4.2 LTS / 5.0; el proyecto usa una versión superior compatible y soportada.
