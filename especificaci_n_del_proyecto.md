# 🛠️ Especificación del Proyecto: Fixpoint
> Plataforma Web Centralizada para la Gestión de Soporte Técnico.  
> Documento único de requerimientos del sistema y fuente de verdad para el desarrollo (Open Code).

---

## 📖 1. Contexto y Problemática
**Organización:** PyME dedicada a comercialización y mantenimiento de equipos TI.

**Problema:** Falta de un canal único para la recepción y seguimiento de solicitudes de soporte. Las peticiones informales provocan pérdida de información, tiempos de respuesta prolongados y nulo seguimiento.
**Consecuencias:** Insatisfacción del cliente, duplicidad de trabajo e incumplimiento de tiempos de respuesta.

**Solución (Fixpoint):** Aplicación web centralizada (Django) para conectar las necesidades de los usuarios con el servicio técnico de forma organizada y transparente.

---

## 🎯 2. Alcance del Proyecto
### ✅ Incluido (In-Scope)
- Registro de incidencias (título, descripción, prioridad) y consulta de estado en tiempo real para **Clientes**.
- Panel de administración para gestión de usuarios y asignación formal de tickets para **Administradores**.
- Tablero de tickets asignados, actualización de estados, comentarios internos/públicos y cierre de resolución para **Agentes**.
- **Nota de diseño:** Todo el flujo y notificaciones se mantienen 100% internos dentro del sistema (campana de notificaciones).

### ❌ Exclusiones (Out-of-Scope)
- Aplicaciones móviles nativas.
- Integración con APIs externas (WhatsApp, SMS, correos electrónicos automatizados).
- Pasarelas de pago y control de inventario físico.

---

## 💻 3. Stack Tecnológico
- **Backend:** Python 3.11+, Django Web Framework (v4.2 LTS / 5.0) - Arquitectura MVT.
- **Base de Datos:** SQLite3 (Desarrollo local).
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5 / Tailwind CSS.
- **Control de Versiones:** Git, GitHub / GitLab.
- **Entorno:** Virtualenv / Pipenv.

---

## 👥 4. Roles del Sistema

| Rol | Descripción | Permisos Básicos |
|---|---|---|
| **Visitante** | Usuario sin sesión activa. | Solo puede registrarse e iniciar sesión. Al registrarse, se le asigna el rol `cliente`. |
| **Cliente** | Usuario final que reporta fallas. | Crea tickets y da seguimiento exclusivo a los suyos. |
| **Agente** | Técnico de soporte. | Atiende **únicamente** los tickets que el Admin le asignó. |
| **Admin** | Administrador del sistema. | Administra usuarios, asigna agentes y tiene acceso global a los tickets. |

> ⚠️ **Nota:** El rol es excluyente. Un usuario tiene exactamente un rol a la vez.

---

## 📜 5. Reglas de Negocio Transversales

| ID | Regla |
|---|---|
| **RN-01** | `email` es obligatorio, único y es el identificador de inicio de sesión. |
| **RN-02** | `username` es obligatorio y único. |
| **RN-03** | La contraseña **nunca** se almacena en texto plano (se usa el hasher de Django). |
| **RN-04** | Todo ticket nace con estado `Nuevo` y **sin** agente asignado. |
| **RN-05** | El código visible de un ticket es `TKT-` + `id` con 3 dígitos (ej. `TKT-001`). |
| **RN-06** | Solo un usuario con rol `agente` puede ser asignado como responsable de un ticket. |
| **RN-07** | Un ticket **cerrado** es de solo lectura (sin cambios de estado ni comentarios), salvo reapertura por Admin. |
| **RN-08** | El cierre de un ticket exige una `resolucion` no vacía (mínimo 10 caracteres). |
| **RN-09** | Aislamiento: Un cliente nunca puede acceder a tickets de otro cliente (HTTP 403). |
| **RN-10** | Aislamiento: Un agente nunca puede acceder a tickets no asignados a él (HTTP 403). |
| **RN-15** | Los comentarios de seguimiento son **inmutables** una vez creados. |

---

## ⚙️ 6. Requerimientos Funcionales (RF)

### Autenticación y Cuentas
- **RF-01 (DEBE):** Visitante puede registrarse y se le asigna rol `cliente` por defecto.
- **RF-02 (DEBE):** Iniciar sesión de forma segura y redirigir al dashboard según el rol.
- **RF-04 (DEBERÍA):** Usuario autenticado puede cambiar su contraseña desde el sistema.

### Gestión de Usuarios (Admin)
- **RF-07 al RF-11 (DEBE):** Admin puede crear usuarios, editar roles, activar/desactivar cuentas, restablecer contraseñas y no puede auto-eliminarse.
- **RF-12 (DEBERÍA):** Al desactivar un agente, sus tickets abiertos regresan a estado `Nuevo` y sin asignar.

### Ciclo de Vida del Ticket
- **RF-13 (DEBE):** Cliente crea ticket (título, descripción, prioridad).
- **RF-18 (DEBERÍA):** Cliente puede editar o cancelar su ticket **solo** si sigue en estado `Nuevo`.
- **RF-21 (DEBE):** Admin asigna o reasigna un ticket a un Agente.
- **RF-23 (DEBE):** Todos los roles involucrados pueden agregar comentarios cronológicos.
- **RF-27 (DEBE):** Cambios de estado validados estrictamente por la **Máquina de Estados**.
- **RF-28 (DEBE):** Cierre del ticket obliga a registrar un texto de resolución.

---

## 🔄 7. Máquina de Estados

El ciclo de vida del ticket es estricto. Cualquier transición no listada aquí será rechazada por el backend.

**Flujo normal:** `Nuevo` ➔ `Asignado` ➔ `En Proceso` ➔ `Resuelto` ➔ `Cerrado`.

| Estado Actual | Transición Permitida | Ejecutado por | Condición |
|---|---|---|---|
| `Nuevo` | `Asignado` | Admin | Al asignar un agente. |
| `Nuevo` | `Cancelado` | Cliente | Cancelación manual por el creador. |
| `Asignado` | `En Proceso` | Agente / Admin | Al iniciar el trabajo. |
| `En Proceso` | `Resuelto` | Agente / Admin | Problema solucionado temporalmente. |
| `Resuelto` | `Cerrado` | Agente / Admin | Confirmación final (Requiere resolución). |
| `Resuelto` | `En Proceso` | Agente / Admin | Si la solución inicial falló. |
| `Cerrado` | `En Proceso` | Admin | Reapertura manual justificada. |

---

## 🛡️ 8. Matriz de Permisos (RBAC)

| Acción | Cliente | Agente | Admin |
|---|:---:|:---:|:---:|
| Crear Ticket | ✅ | ❌ | ❌ |
| Ver Tickets | Solo Propios | Solo Asignados | Todos |
| Cancelar Ticket | Solo estado `Nuevo` | ❌ | ❌ |
| Asignar Agente | ❌ | ❌ | ✅ |
| Comentar | Propios | Asignados | Todos |
| Cambiar Estado | ❌ | Asignados | Todos |
| Cerrar / Resolver | ❌ | Asignados | Todos |
| Gestionar Usuarios | ❌ | ❌ | ✅ |

---

## 🖥️ 9. Prototipo de Pantallas y Base de Datos

### Prototipo de Interfaz UI/UX
*Diseño responsivo con un panel lateral (Sidebar) y métricas clave.*
![Prototipo de Pantallas](image_42b07a.png)

### Diagrama Entidad-Relación (ERD)
*Modelo relacional para Usuarios, Tickets y tabla pivote de Seguimientos (Comentarios).*
![Modelo de Base de Datos](image_42b09d.png)