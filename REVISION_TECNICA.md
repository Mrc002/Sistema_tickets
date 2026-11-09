# Revisión Técnica del Software — Fixpoint

**Proyecto:** Fixpoint — Plataforma Web Centralizada para la Gestión de Soporte Técnico  
**Organización:** PyME de comercialización y mantenimiento de equipos TI  
**Documento revisado:** `especificaci_n_del_proyecto.md` (fuente de verdad) y su derivado `REQUERIMIENTOS.md`  
**Código revisado:** módulo de ciclo de vida y asignación de tickets (`models.py`, `forms.py`, `views.py`, `services.py`, `admin.py`)  
**Fecha de revisión:** 03/11/2026  
**Modalidad:** revisión técnica de escritorio con listas de verificación, inspección de código, pruebas automatizadas y verificación empírica con reversión de datos  
**Alcance funcional:** RF-12, RF-21, RF-27, RF-28, RN-06, RN-07 y RN-08

---

## Resumen ejecutivo

Se revisaron dos artefactos: el documento de especificación (requerimientos funcionales y reglas de negocio) y el componente que implementa el ciclo de vida del ticket. Se aplicaron **20 criterios** al documento y **20 criterios** al código.

| Checklist | Cumple | No cumple | No aplica | Total |
|---|---:|---:|---:|---:|
| Requerimientos | 6 | 14 | 0 | 20 |
| Código fuente | 8 | 12 | 0 | 20 |

Se registraron **24 hallazgos**: 2 de severidad crítica, 5 mayores y 17 menores. Los dos hallazgos críticos son:

1. **HC-01:** la máquina de estados implementada permite cinco transiciones que la especificación prohíbe expresamente.
2. **HC-04:** el panel de administración de Django permite saltarse las reglas RN-06, RN-07, RN-08, RN-15 y RF-27 sin validación alguna.

Ningún hallazgo fue inferido sin evidencia: todos se respaldan con ubicación exacta (`archivo:línea` o `documento:línea`), inspección directa, prueba automatizada o reproducción controlada. La reproducción empírica se ejecutó dentro de una transacción revertida, por lo que no se modificó la base de datos de desarrollo.

---

## 1. Marco conceptual: la revisión técnica en el aseguramiento de la calidad

### 1.1 ¿Qué es una revisión técnica y cuál es su objetivo?

Una **revisión técnica** es un examen sistemático, documentado y colaborativo de un producto de trabajo de software —requerimientos, diseño, código, pruebas, documentación o configuración— realizado por personal calificado distinto de quien lo produjo. Su propósito es **identificar defectos, verificar la conformidad con la especificación y los estándares, y recomendar mejoras** antes de que el producto avance a la siguiente fase (IEEE 1028; ISO/IEC/IEEE 20246).

A diferencia de las pruebas, la revisión es una técnica **estática**: no requiere ejecutar el sistema y puede aplicarse a artefactos que aún no son ejecutables, como la especificación de requerimientos. Las pruebas observan el comportamiento; la revisión examina el artefacto y su correspondencia con lo esperado. Ambas técnicas son complementarias.

**Objetivos principales:**

- Detectar defectos de forma temprana, cuando corregirlos es más barato.
- Verificar que el artefacto cumple la especificación, la arquitectura y las convenciones acordadas.
- Evaluar la calidad del artefacto: claridad, completitud, consistencia, verificabilidad y mantenibilidad.
- Reducir el riesgo de retrabajo, incidentes en producción y defectos que escapan a las pruebas.
- Alinear al equipo y transferir conocimiento sobre el producto.
- Generar evidencia objetiva y métricas para la mejora continua del proceso.

### 1.2 Tipos de revisiones de software

| Tipo | Quién la dirige | Formalidad | Propósito principal | Salida típica |
|---|---|---|---|---|
| Revisión informal (*peer review*) | Un colega o el propio autor | Baja | Detección rápida de errores evidentes | Comentarios informales |
| *Walkthrough* | El autor | Media | Explicar el artefacto y detectar problemas mientras se recorre | Observaciones y dudas |
| **Revisión técnica** | Un moderador con pares técnicos | Media-alta | Evaluar la calidad técnica y la conformidad con la especificación | Informe de revisión con hallazgos |
| Inspección formal | Moderador con inspectores y roles definidos | Alta | Detección sistemática con criterios de entrada/salida, checklist y métricas | Registro formal de defectos |
| Revisión de gestión | Responsables del proyecto | Media | Evaluar avance, riesgos, costos y decisiones | Acta de decisiones |
| Auditoría | Auditor independiente | Alta | Verificar cumplimiento de estándares, contratos o normativas | Informe de auditoría |

Además de estos tipos, existen prácticas complementarias: revisión entre pares (*pair programming*), revisión de código, análisis estático automatizado y revisión de cambios (*pull request review*). Las herramientas de análisis estático **complementan** la revisión, pero no sustituyen el juicio humano sobre la correspondencia entre lo especificado y lo implementado.

### 1.3 ¿Qué aspectos de un proyecto de software se pueden revisar?

| Artefacto | Qué se revisa | Ejemplo en Fixpoint |
|---|---|---|
| Requerimientos | Claridad, completitud, consistencia, verificabilidad, trazabilidad | `especificaci_n_del_proyecto.md`, reglas RN y RF |
| Diseño y arquitectura | Coherencia con requisitos, separación de capas, acoplamiento | Patrón MVT de Django, capa `services.py` |
| Código fuente | Nomenclatura, formato, responsabilidades, validaciones, seguridad | `tickets/models.py`, `tickets/views.py` |
| Modelo de datos | Entidades, relaciones, integridad, migraciones | `Ticket`, `Seguimiento`, `Notificacion` |
| Pruebas | Cobertura, casos límite, calidad de aserciones | `tickets/tests.py` (40 pruebas) |
| Interfaz y experiencia de usuario | Claridad, accesibilidad, responsividad, mensajes | Plantillas Bootstrap 5 |
| Documentación | Exactitud, actualización, utilidad para el equipo | `README.md`, `DIAGRAMA_ER.md` |
| Configuración y dependencias | Versiones, reproducibilidad, variables de entorno | `requirements.txt`, `.env.example` |
| Seguridad | Autenticación, autorización, CSRF, validación de entradas | Login por email, RBAC, `CsrfViewMiddleware` |
| Rendimiento y operación | Consultas, paginación, tiempos de respuesta | `select_related`, paginación de 20 |
| Despliegue y mantenibilidad | Facilidad de instalación, migraciones, observabilidad | `manage.py`, migraciones 0001–0003 |

### 1.4 Beneficios de una revisión técnica

| Beneficio | Cómo se manifiesta |
|---|---|
| Detección temprana | Un defecto de requerimientos se corrige antes de escribir código; un defecto de estado se detecta antes de operar el sistema. |
| Reducción de costos | El costo de corregir un defecto crece con cada fase; la revisión lo intercepta en la fase donde nace. |
| Mayor calidad del producto | Requerimientos verificables, código legible, reglas de negocio consistentes. |
| Trazabilidad | Permite comprobar que cada requisito tiene implementación y prueba. |
| Consistencia | Unifica terminología, convenciones y criterios entre documentos y código. |
| Reducción de riesgo | Identifica incumplimientos de seguridad, integridad y reglas críticas antes de producción. |
| Mantenibilidad | Código con responsabilidades claras, nombres descriptivos y documentación útil. |
| Conocimiento compartido | El equipo comprende el producto y evita dependencias de una sola persona. |
| Evidencia y métricas | Los hallazgos permiten medir densidad de defectos y priorizar la mejora del proceso. |
| Confianza del cliente | Demuestra que el producto fue examinado con criterios objetivos y no solo probado. |

El beneficio depende de la preparación individual, de una lista de verificación adecuada, de un moderador que evite desviaciones y de un seguimiento real de las acciones correctivas.

### 1.5 Proceso y roles de una revisión técnica

1. **Planificación:** definir alcance, artefactos, criterios y participantes.
2. **Apertura:** explicar el objetivo y el contexto a los revisores.
3. **Preparación individual:** cada revisor aplica la checklist y documenta hallazgos.
4. **Reunión de revisión:** se consolidan hallazgos, se eliminan falsos positivos y se clasifica la severidad.
5. **Retrabajo:** el autor corrige o justifica cada hallazgo.
6. **Seguimiento:** se verifica el cierre y se registran métricas.

Roles habituales: **moderador** (conduce y garantiza el proceso), **autor** (explica y corrige), **revisores** (examinan con criterio técnico) y **secretario** (registra hallazgos y decisiones).

En esta revisión se aplicó un enfoque de **revisión técnica con checklist**, inspirado en la inspección formal, pero adaptado a un equipo pequeño: un revisor actuó como moderador y secretario, sin reunión formal. Esta decisión se registra como limitación en la sección 5.8.

---

## 2. Elementos seleccionados para la revisión

### 2.1 Nombre y propósito del proyecto

**Fixpoint** es una aplicación web desarrollada para una PyME dedicada a la comercialización y mantenimiento de equipos TI. Su propósito es centralizar la recepción y el seguimiento de solicitudes de soporte técnico, sustituyendo las peticiones informales por un canal único con trazabilidad, estados y responsables.

El sistema se implementó con **Django 6.1.2**, **SQLite3** en desarrollo y **Bootstrap 5**, bajo el patrón MVT. El documento `especificaci_n_del_proyecto.md` es la fuente de verdad; `REQUERIMIENTOS.md` resume esa especificación y agrega el estado de implementación.

### 2.2 Principales funcionalidades del sistema

- **Autenticación y cuentas:** registro público de clientes, inicio de sesión por correo electrónico, cambio de contraseña y perfil editable.
- **Clientes:** creación de tickets con título, descripción, categoría y prioridad; consulta de estado; edición y cancelación mientras el ticket esté en estado `Nuevo`; comentarios públicos.
- **Agentes:** tablero de tickets asignados; cambio de estado; comentarios públicos e internos; cierre con resolución obligatoria.
- **Administradores:** gestión de usuarios desde el panel de Django; asignación y reasignación de agentes; acceso global a tickets; exportación CSV.
- **Notificaciones internas:** campana con contador de no leídas, bandeja paginada y marca de lectura; sin correos automáticos.
- **Funciones adicionales:** categorías, SLA por prioridad, filtros, paginación, historial automático de cambios, reapertura de tickets cerrados y auditoría.

### 2.3 Requerimientos que serán revisados

Se seleccionaron los requerimientos que concentran las reglas de negocio más críticas y que atraviesan a todos los roles:

| ID | Enunciado según la especificación | Prioridad | Ubicación |
|---|---|---|---|
| **RF-12** | Al desactivar un agente, sus tickets abiertos regresan a estado `Nuevo` y sin asignar. | DEBERÍA | `especificaci_n_del_proyecto.md:80` |
| **RF-21** | El Admin asigna o reasigna un ticket a un Agente. | DEBE | `especificaci_n_del_proyecto.md:85` |
| **RF-27** | Los cambios de estado se validan estrictamente con la máquina de estados. | DEBE | `especificaci_n_del_proyecto.md:87` |
| **RF-28** | El cierre del ticket obliga a registrar un texto de resolución. | DEBE | `especificaci_n_del_proyecto.md:88` |
| **RN-06** | Solo un usuario con rol `agente` puede ser asignado como responsable. | Transversal | `especificaci_n_del_proyecto.md:62` |
| **RN-07** | Un ticket cerrado es de solo lectura, salvo reapertura por el Admin. | Transversal | `especificaci_n_del_proyecto.md:63` |
| **RN-08** | El cierre exige una `resolucion` no vacía de mínimo 10 caracteres. | Transversal | `especificaci_n_del_proyecto.md:64` |

**Criterio de selección:** son requisitos de alta prioridad, con impacto directo en la integridad del flujo de soporte, verificables mediante pruebas y con implementación identificable en el código. Además, involucran a los tres roles y a la capa de administración.

### 2.4 Módulo, clase o componente de código seleccionado

Se seleccionó el **componente de ciclo de vida y asignación de tickets**, compuesto por los siguientes elementos:

| Archivo | Elemento | Líneas | Función |
|---|---|---|---|
| `tickets/models.py` | Clase `Ticket` (estados, transiciones, `puede_transicionar_a`, `cerrar`, `reabrir`) | 50–165 | Define el modelo de dominio y la máquina de estados. |
| `tickets/forms.py` | `AsignacionForm` | 88–99 | Restringe la asignación a agentes activos. |
| `tickets/forms.py` | `CierreForm` | 102–121 | Valida la resolución mínima de 10 caracteres. |
| `tickets/views.py` | `detalle_ticket` | 182–367 | Orquesta comentarios, cambios de estado, prioridad, cierre, reapertura y cancelación. |
| `tickets/views.py` | `asignar_ticket` | 370–388 | Punto de entrada del Admin para asignar o reasignar. |
| `tickets/services.py` | `registrar_evento` | 6–14 | Registra eventos de auditoría en el historial. |
| `tickets/services.py` | `liberar_tickets_de_agente` | 105–121 | Libera tickets al desactivar o eliminar un agente. |
| `tickets/services.py` | `asignar_agente` | 124–145 | Valida rol y estado, asigna y notifica. |
| `tickets/admin.py` | `TicketAdmin`, `SeguimientoInline`, `SeguimientoAdmin` | 59–87 | Capa de administración de los mismos datos y reglas. |

La inclusión de `admin.py` es deliberada: es un punto de entrada real al dominio y, por tanto, debe cumplir las mismas reglas que la interfaz web.

### 2.5 Justificación de los elementos seleccionados

- **Cobertura de extremo a extremo:** el componente va del modelo (`Ticket`) al formulario, la vista, el servicio y el panel de administración. Permite comprobar si la regla especificada se mantiene en todas las capas.
- **Criticidad funcional:** RF-27 y RN-08 son reglas centrales del negocio; un fallo aquí permite cerrar tickets sin resolución o saltarse el flujo aprobado.
- **Riesgo de regresión:** la máquina de estados y la liberación de agentes se modificaron durante la evolución del proyecto, lo que incrementa la probabilidad de inconsistencias.
- **Verificabilidad:** el módulo tiene pruebas automatizadas y es posible reproducir sus reglas de forma controlada.
- **Tamaño manejable:** permite una revisión exhaustiva en lugar de un muestreo superficial.
- **Correspondencia requisito–código:** cada requerimiento seleccionado tiene una implementación identificable, lo que hace posible comprobar la conformidad y no solo la calidad sintáctica.

### 2.6 Correspondencia entre requerimientos y código

| Requerimiento | Modelo | Formulario | Vista | Servicio | Prueba relacionada |
|---|---|---|---|---|---|
| RF-12 | `Ticket.agente`, `Ticket.estado` | — | `admin.save_model` | `liberar_tickets_de_agente` | `tests.py:286–289` |
| RF-21 | `Ticket.agente` | `AsignacionForm` | `asignar_ticket` | `asignar_agente` | `tests.py:264–284` |
| RF-27 | `Ticket.TRANSICIONES`, `puede_transicionar_a` | — | `detalle_ticket` | — | `tests.py:179–204` |
| RF-28 | `Ticket.cerrar` | `CierreForm` | `detalle_ticket` | `registrar_evento` | `tests.py:216–230` |
| RN-06 | `Ticket.agente` (FK) | `AsignacionForm` | `asignar_ticket` | `asignar_agente` | `tests.py:278–284` |
| RN-07 | `Ticket.ESTADOS_FINALES` | — | `detalle_ticket` (bloqueo) | — | `tests.py:232–241` |
| RN-08 | `Ticket.resolucion` | `CierreForm` | `detalle_ticket` | — | `tests.py:216–230` |

---

## 3. Metodología de la revisión

> El enunciado numera los pasos 1, 2, 4 y 5. Se incorpora este apartado 3 como metodología para mantener la secuencia y explicar cómo se aplicaron las listas de verificación.

### 3.1 Instrumentos

- **Checklist de requerimientos:** 20 criterios aplicados a `especificaci_n_del_proyecto.md`.
- **Checklist de código:** 20 criterios aplicados al componente seleccionado.
- **Inspección directa:** lectura completa de los archivos y búsqueda de patrones (`raw`, `atomic`, `|safe`, `send_mail`, etc.).
- **Pruebas automatizadas:** `python manage.py test` (40 pruebas).
- **Verificación empírica controlada:** script con `transaction.atomic()` y `transaction.set_rollback(True)` para reproducir comportamientos sin persistir cambios.
- **Verificación de configuración:** `manage.py check`, `makemigrations --check --dry-run`, longitud de líneas y presencia de archivos referenciados.

### 3.2 Procedimiento

1. Leer la especificación y localizar los RF/RN del alcance.
2. Rastrear cada requerimiento hasta su implementación (modelo, formulario, vista, servicio, prueba).
3. Aplicar la checklist de requerimientos al documento.
4. Aplicar la checklist de código al componente.
5. Verificar cada sospecha con inspección o reproducción antes de registrarla.
6. Clasificar el resultado como **Cumple**, **No cumple** o **No aplica**, con evidencia y ubicación exacta.
7. Registrar los hallazgos y proponer acciones correctivas.
8. Revertir cualquier cambio de datos producido por la verificación empírica.

### 3.3 Escalas utilizadas

**Resultado del criterio:**

- **Cumple:** el criterio se satisface y existe evidencia verificable.
- **No cumple:** existe una desviación comprobable.
- **No aplica:** el criterio no corresponde al artefacto o al alcance, con justificación explícita.

**Severidad del hallazgo:**

- **Crítica:** incumple una regla central, permite corrupción de datos o bloquea la aceptación del producto.
- **Mayor:** incumple un requisito relevante o deja una brecha funcional significativa.
- **Menor:** afecta mantenibilidad, legibilidad, robustez o cobertura, sin romper el flujo principal.

### 3.4 Reglas de evidencia

- Todo hallazgo debe indicar `archivo:línea` o `documento:línea`.
- Las afirmaciones sobre comportamiento se respaldan con una prueba existente o con una reproducción controlada.
- No se registran defectos hipotéticos, de estilo subjetivo sin criterio, ni problemas que no puedan comprobarse.
- Los números de línea corresponden a la revisión revisada el 03/11/2026. Al no existir repositorio Git (ver OBS-02), no es posible citar un hash de confirmación.

---

## 4. Listas de verificación

### 4.1 Checklist para la revisión de requerimientos (20 criterios)

El checklist combina **10 criterios base** (aplicables a cualquier documento de requisitos) con **10 criterios de ampliación** adaptados a este proyecto. Se aplica a `especificaci_n_del_proyecto.md`.

| # | Criterio de revisión | Qué se verifica |
|---:|---|---|
| 1 | ¿Cada requerimiento cuenta con un identificador único y estable? | Un ID por requisito, sin agrupaciones ni saltos injustificados. |
| 2 | ¿Está redactado de manera clara y comprensible? | Un lector técnico puede entenderlo sin ambigüedad. |
| 3 | ¿Describe una necesidad o funcionalidad específica? | El requisito expresa un comportamiento concreto, no un deseo general. |
| 4 | ¿Evita términos ambiguos o interpretaciones diferentes? | No usa expresiones como «tiempo real» o «seguro» sin definirlas. |
| 5 | ¿Es verificable mediante una prueba o criterio objetivo? | Es posible diseñar una prueba que determine su cumplimiento. |
| 6 | ¿Es consistente con los demás requerimientos, reglas y matriz RBAC? | No contradice otras reglas ni permisos. |
| 7 | ¿Es necesario para cumplir los objetivos del sistema? | Contribuye al problema y al alcance definidos. |
| 8 | ¿Es factible de implementar con los recursos y el stack disponibles? | No exige tecnología o esfuerzo fuera de alcance. |
| 9 | ¿Tiene criterios de aceptación o condiciones de cumplimiento? | Define cuándo se considera satisfecho. |
| 10 | ¿Identifica claramente al actor o rol responsable? | El usuario, rol o sistema involucrado es explícito. |
| 11 | ¿Tiene una prioridad asignada de forma individual? | DEBE, DEBERÍA o equivalente, por requisito. |
| 12 | ¿Se identifican requerimientos no funcionales medibles? | Rendimiento, seguridad, usabilidad, disponibilidad, respaldo y privacidad con métricas. |
| 13 | ¿El alcance incluido y excluido está delimitado? | El documento distingue qué entra y qué no. |
| 14 | ¿Los roles y permisos están definidos y son coherentes? | Existe una matriz de roles y permisos consistente. |
| 15 | ¿Existe trazabilidad entre requisitos, alcance, diseño y pruebas? | Matriz de trazabilidad o vínculos explícitos. |
| 16 | ¿Las referencias a prototipos, diagramas e imágenes son válidas? | Los archivos referenciados existen y son accesibles. |
| 17 | ¿La terminología es uniforme y existe un glosario del dominio? | Los mismos conceptos usan los mismos nombres y están definidos. |
| 18 | ¿Se definen los estados, las transiciones y el modelo de datos? | La máquina de estados y las entidades están completas y sin ambigüedad. |
| 19 | ¿El documento tiene plantilla uniforme, metadatos y control de versión? | Autor, fecha, versión, estado, historial y estructura homogénea. |
| 20 | ¿Se especifican las notificaciones internas (evento, destinatario y momento)? | Quién recibe qué aviso y en qué evento. |

### 4.2 Checklist para la revisión del código fuente (20 criterios)

El checklist combina **10 criterios base** de revisión de código con **10 criterios de ampliación** centrados en las reglas de negocio del proyecto. Se aplica al componente de ciclo de vida y asignación de tickets.

| # | Criterio de revisión | Qué se verifica |
|---:|---|---|
| 1 | ¿El código cumple las convenciones de nomenclatura y formato del lenguaje (PEP 8)? | Longitud de línea, imports, espacios, formato. |
| 2 | ¿Las clases, funciones y variables tienen nombres claros y descriptivos? | El nombre expresa intención sin necesidad de comentario. |
| 3 | ¿La indentación y el formato son consistentes? | Sin tabulaciones mezcladas, bloques alineados. |
| 4 | ¿Cada función o método tiene una responsabilidad clara y acotada? | Una función no concentra múltiples flujos independientes. |
| 5 | ¿Se evita la duplicación innecesaria de código? | No hay bloques equivalentes repetidos. |
| 6 | ¿Se utilizan adecuadamente las estructuras de control y los ciclos? | Condicionales, iteraciones y retornos tempranos son correctos. |
| 7 | ¿Se validan las entradas de datos cuando es necesario? | Formularios, vistas y servicios rechazan datos inválidos. |
| 8 | ¿Se manejan los errores y se conservan los datos del formulario? | 404, 403, validación y errores específicos sin perder lo escrito. |
| 9 | ¿El código contiene comentarios o docstrings cuando son necesarios? | Las funciones complejas explican su propósito. |
| 10 | ¿La implementación corresponde con el requerimiento especificado? | Existe correspondencia verificable RF/RN ↔ código. |
| 11 | ¿Se usan constantes en lugar de literales mágicos? | Estados y prioridades están centralizados. |
| 12 | ¿Se utiliza el ORM de Django y se previene la inyección SQL? | Sin SQL crudo; consultas parametrizadas y CSV citado. |
| 13 | ¿El control de acceso por rol se aplica en todas las capas? | No solo en la vista web, también en el panel de administración. |
| 14 | ¿Se aplica autorización por objeto (cliente dueño, agente asignado)? | Un usuario no accede a tickets ajenos. |
| 15 | ¿Las reglas de negocio se validan en la capa de dominio? | El modelo o servicio impide estados y cierres inválidos. |
| 16 | ¿La máquina de estados es íntegra y consistente con la especificación? | Solo se permiten las transiciones documentadas. |
| 17 | ¿Las operaciones de múltiples escrituras son atómicas? | Un fallo intermedio no deja datos inconsistentes. |
| 18 | ¿Las migraciones reflejan el modelo y están aplicadas? | No hay cambios pendientes ni deriva de esquema. |
| 19 | ¿Las pruebas cubren las reglas y los casos límite en la capa correcta? | Pruebas positivas, negativas, de modelo/servicio y de vista. |
| 20 | ¿El modelo impone restricciones de integridad en la base de datos? | `unique`, `check`, claves foráneas y campos no nulos. |

---

## 5. Aplicación de la revisión técnica

### 5.1 Resultados — Checklist de requerimientos

Aplicada a `especificaci_n_del_proyecto.md` (fuente de verdad). La columna «Ubicación» usa `documento:línea`.

| # | Criterio | Resultado | Evidencia | Ubicación |
|---:|---|---|---|---|
| 1 | Identificador único | ❌ No cumple | «RF-07 al RF-11» agrupa cinco requisitos bajo un solo identificador; faltan RF-03, 05, 06, 14–17, 19–20, 22, 24–26 y 29+ sin explicación. | `especificaci_n_del_proyecto.md:79`, `74–88` |
| 2 | Claridad | ❌ No cumple | «seguimiento exclusivo a los suyos», «Problema solucionado temporalmente», «cierre de resolución» admiten más de una lectura. | `45`, `103`, `21` |
| 3 | Necesidad específica | ✅ Cumple | RF-13 define los campos del ticket; RF-28 exige resolución; RF-21 define la asignación. | `83`, `88`, `85` |
| 4 | Sin ambigüedad | ❌ No cumple | «en tiempo real», «de forma segura», «100 % internos» y «justificada» no se definen ni se acotan. | `19`, `75`, `22`, `106` |
| 5 | Verificable | ❌ No cumple | Ningún RF incluye criterio de aceptación; RF-02 exige seguridad sin parámetro medible. | `74–88` |
| 6 | Consistencia | ❌ No cumple | RN-07 prohíbe comentar tickets cerrados; la matriz RBAC permite «Comentar: Admin Todos» sin excepción ni precedencia. | `63` vs. `118` |
| 7 | Necesario para los objetivos | ✅ Cumple | Los RF seleccionados cubren registro, asignación, estado y cierre del alcance. | `19–21` |
| 8 | Factible | ✅ Cumple | El stack declarado y la implementación existente permiten cumplirlos; las 40 pruebas se ejecutan correctamente. | `31–36`, `README.md` |
| 9 | Criterios de aceptación | ❌ No cumple | No hay condiciones de aceptación por requisito; la tabla de estados solo describe condiciones de transición. | `98–106` |
| 10 | Actor identificado | ✅ Cumple | Los RF indican Visitante, Usuario, Admin, Cliente o roles involucrados. | `74–88` |
| 11 | Prioridad individual | ❌ No cumple | Solo los RF tienen DEBE/DEBERÍA; las RN y la matriz RBAC no tienen prioridad y cinco RF comparten una sola. | `74–88`, `57–67`, `110–121` |
| 12 | RNF medibles | ❌ No cumple | No existe sección de RNF; no se especifican rendimiento, seguridad, usabilidad, disponibilidad, respaldo ni privacidad con métricas. | `1–133`, `31–36` |
| 13 | Alcance delimitado | ✅ Cumple | Sección «Incluido» y «Exclusiones» explícitas. | `17–27` |
| 14 | Roles y permisos | ✅ Cumple | Cuatro roles definidos y matriz RBAC completa. | `40–49`, `110–121` |
| 15 | Trazabilidad | ❌ No cumple | No hay matriz que vincule RF con alcance, diseño, código o pruebas. | `1–133` |
| 16 | Referencias visuales válidas | ❌ No cumple | Se referencian `image_42b07a.png` e `image_42b09d.png`; ninguno existe en el repositorio. | `129`, `133` |
| 17 | Terminología y glosario | ❌ No cumple | Cliente, Agente y Admin se usan de forma consistente, pero no hay glosario que defina «resolución», «seguimiento» ni «cierre». | `21`, `45`, `103` |
| 18 | Estados y modelo de datos | ❌ No cumple | `Cancelado` solo aparece como destino y el modelo de datos se referencia en una imagen ausente; no hay entidades ni relaciones en texto. | `101`, `131–133` |
| 19 | Metadatos y control de versión | ❌ No cumple | El encabezado solo tiene título y subtítulo; no hay autor, fecha, versión, estado ni historial de cambios, y se mezclan viñetas con tablas. | `1–3`, `57–67`, `74–88` |
| 20 | Notificaciones internas | ❌ No cumple | Solo se indica que las notificaciones son «100 % internas»; no se definen eventos, destinatarios ni momento de emisión. | `22` |

### 5.2 Resultados — Checklist de código fuente

Aplicada al componente de ciclo de vida y asignación. La columna «Ubicación» usa `archivo:línea`.

| # | Criterio | Resultado | Evidencia | Ubicación |
|---:|---|---|---|---|
| 1 | Convenciones y formato (PEP 8) | ❌ No cumple | 37 líneas superan 79 caracteres: 5 en `models.py` (máx. 94), 20 en `views.py` (máx. 97), 8 en `forms.py` (máx. 93), 2 en `services.py` (máx. 92) y 2 en `admin.py` (máx. 99). No hay configuración de estilo. | `models.py:113`, `views.py:46`, `admin.py:11` |
| 2 | Nombres descriptivos | ✅ Cumple | `TRANSICIONES`, `puede_transicionar_a`, `liberar_tickets_de_agente`, `notificar_cambio_estado` expresan intención. | `models.py:92`, `151`; `services.py:58`, `105` |
| 3 | Indentación y formato | ✅ Cumple | 4 espacios, sin tabulaciones (0 ocurrencias) y finales de línea consistentes. | Archivos revisados |
| 4 | Responsabilidad única | ❌ No cumple | `detalle_ticket` ocupa 185 líneas y atiende seis acciones distintas en una sola función. | `views.py:182–367` |
| 5 | Duplicación | ❌ No cumple | El recorrido de destinatarios se repite en dos funciones; la longitud mínima se valida dos veces en `CierreForm`. | `services.py:63–70` y `75–82`; `forms.py:105` y `117` |
| 6 | Estructuras de control | ✅ Cumple | Despacho por acción con `if/elif`, retornos tempranos y bucles sobre querysets. | `views.py:197–335`; `services.py:110–121` |
| 7 | Validación de entradas | ✅ Cumple | `clean_titulo`, `clean_descripcion`, `clean_comentario`, `clean_resolucion`; la vista valida estado y permisos. | `forms.py:45–57`, `81–121`; `views.py:228–239` |
| 8 | Errores y conservación de datos | ❌ No cumple | Hay `get_object_or_404` y captura de `ValueError`, pero ante un formulario inválido se redirige con un mensaje genérico y se pierden los datos y los errores por campo. | `views.py:220–222`, `291–296`, `314–317`, `344–346` |
| 9 | Comentarios y docstrings | ❌ No cumple | Solo `notificaciones` y `abrir_notificacion` tienen docstring; `detalle_ticket`, `crear_ticket` y `asignar_ticket` no lo tienen. | `views.py:134`, `183`, `371`, `446`, `465` |
| 10 | Correspondencia con el requerimiento | ❌ No cumple | La máquina de estados permite transiciones no especificadas y la liberación de agentes no cumple RF-12 en todos los casos. | `models.py:92–99`; `services.py:110–114` |
| 11 | Constantes en lugar de literales | ✅ Cumple | Estados, prioridades y categorías están centralizados como constantes de clase. | `models.py:51–99` |
| 12 | ORM e inyección | ✅ Cumple | No se encontró `raw`, `extra` ni SQL manual; la exportación usa `csv.writer`, que cita los campos. | `models.py`, `views.py`, `services.py`; `views.py:398–427` |
| 13 | Control de acceso por rol en todas las capas | ❌ No cumple | El panel de administración permite editar estado, agente y resolución sin las validaciones del dominio. | `admin.py:59–87` |
| 14 | Autorización por objeto | ✅ Cumple | `puede_ver_ticket` y filtros por usuario; las pruebas confirman 403 y 404. | `decorators.py:23–29`; `tests.py:84–97`, `446–454` |
| 15 | Reglas de negocio en el dominio | ❌ No cumple | `Ticket.cerrar()` acepta una resolución de 5 caracteres y `asignar_agente` no verifica `is_active`. | `models.py:154–159`; `services.py:126–127` |
| 16 | Máquina de estados íntegra | ❌ No cumple | Se permiten cinco transiciones que la especificación no autoriza. | `models.py:92–99` |
| 17 | Atomicidad | ❌ No cumple | Estado, seguimiento y notificación se guardan en operaciones separadas sin `transaction.atomic()`. | `views.py:241–251`, `282–289`; `services.py:131–144` |
| 18 | Migraciones | ✅ Cumple | Existen 0001–0003, están aplicadas y `makemigrations --check` no detecta cambios. | `tickets/migrations/` |
| 19 | Cobertura y nivel de pruebas | ❌ No cumple | No hay prueba negativa para cierre desde `Nuevo` o `Asignado`; RF-12 solo se prueba con un ticket `Asignado` y las reglas se validan casi solo por HTTP. | `tests.py:216–230`, `286–289`, `233`, `244`, `256`, `271–276` |
| 20 | Integridad en modelo y base de datos | ❌ No cumple | No existen `CheckConstraint` ni `UniqueConstraint`; `resolucion` admite vacío y `estado` es un `CharField` sin restricción de base de datos. | `models.py:108–133`, `245–249` |

### 5.3 Registro de hallazgos

| ID | Severidad | Criterios | Hallazgo | Evidencia y ubicación | Acción recomendada |
|---|---|---|---|---|---|
| **HR-01** | Mayor | 12 | El documento no contiene requerimientos no funcionales ni operativos; solo describe el stack. | `especificaci_n_del_proyecto.md:1–133`; no existe sección de RNF; `31–36` solo enumera tecnología. | Agregar RNF medibles de rendimiento, seguridad, usabilidad, disponibilidad, respaldo, privacidad y accesibilidad. |
| **HR-02** | Mayor | 2, 4, 5, 9 | No hay criterios de aceptación y varios requisitos usan términos no medibles. | «en tiempo real» `19`; «de forma segura» `75`; «100 % internos» `22`; «justificada» `106`; RF `74–88` sin criterios. | Definir criterios de aceptación verificables y un glosario de términos. |
| **HR-03** | Mayor | 1, 11 | Identificadores agrupados, saltos de numeración sin explicación y requisitos no atómicos. | «RF-07 al RF-11» `79`; faltan RF-03, 05, 06, 14–17, 19–20, 22, 24–26 y 29+. | Un identificador por requisito, un requisito por necesidad y registro de requisitos retirados. |
| **HR-04** | Menor | 2, 4, 17 | Expresiones ambiguas y ausencia de glosario que fije su significado. | «seguimiento exclusivo a los suyos» `45`; «Problema solucionado temporalmente» `103`; «cierre de resolución» `21`. | Reescribir con lenguaje preciso y agregar un glosario de dominio. |
| **HR-05** | Menor | 6 | RN-07 y la matriz RBAC se contradicen respecto a comentar tickets cerrados. | RN-07 `63`; fila «Comentar» `118`. | Declarar precedencia y excepción de solo lectura. |
| **HR-06** | Menor | 18 | `Cancelado` no se define como estado terminal ni se documentan sus transiciones. | `101` (solo destino); el código lo trata como terminal en `models.py:87,98`. | Agregar fila de estado y condición de terminalidad. |
| **HR-07** | Menor | 16, 18 | Referencias a imágenes inexistentes y modelo de datos sin descripción textual. | `image_42b07a.png` `129`; `image_42b09d.png` `133`; no hay PNG en la raíz. | Incorporar las imágenes o reemplazarlas por el ERD textual de `DIAGRAMA_ER.md`. |
| **HR-08** | Menor | 15 | No existe matriz de trazabilidad ni mapa de dependencias entre requisitos, diseño, código y pruebas. | Documento completo `1–133`; no hay vínculos RF ↔ prueba ni orden de dependencias. | Crear una matriz de trazabilidad y un mapa de dependencias. |
| **HR-09** | Menor | 19 | El documento carece de plantilla uniforme, metadatos y control de versión. | Encabezado `1–3` sin autor, fecha, versión ni historial; RF en viñetas `74–88` frente a tablas `57–67`, `110–121`. | Adoptar una plantilla de requisitos y registrar versión, autor, fecha y cambios. |
| **HR-10** | Menor | 20 | Las notificaciones internas se mencionan de forma genérica, sin eventos, destinatarios ni momento de emisión. | `22` solo indica «100 % internos»; el detalle aparece en `REQUERIMIENTOS.md:130–143`, no en la fuente de verdad. | Especificar la matriz evento → destinatario → momento y su criterio de aceptación. |
| **HC-01** | Crítica | 10, 16 | La máquina de estados permite transiciones que la especificación prohíbe. | `models.py:92–99` vs. `especificaci_n_del_proyecto.md:94–106`; reproducción empírica; `views.py:350–351`; `tests.py:216–230`. | Alinear la tabla con la especificación o actualizar la especificación y las pruebas; agregar pruebas negativas. |
| **HC-02** | Mayor | 10 | RF-12 se cumple solo parcialmente: los tickets en `En Proceso` quedan en ese estado y sin agente. | `services.py:110–114`; reproducción: «estado: En Proceso, agente: None»; `tests.py:286–289`. | Llevar todos los tickets abiertos a `Nuevo` y probar el caso `En Proceso`. |
| **HC-03** | Mayor | 15 | RN-08 no se valida en el dominio: `Ticket.cerrar()` acepta resoluciones de menos de 10 caracteres. | `models.py:154–159`; `forms.py:102–121`; reproducción con `'corta'` (5 caracteres) que cierra el ticket. | Validar en el modelo o servicio y agregar prueba unitaria. |
| **HC-04** | Crítica | 13 | El admin de Django permite saltarse RN-06, RN-07, RN-08, RN-15 y RF-27. | `admin.py:59–63` (comentarios editables), `66–81` (`estado`, `agente`, `resolucion` editables sin validación), `84–87`. | Hacer de solo lectura los campos críticos, limitar el queryset de agentes y validar en `save_model`/formularios del admin. |
| **HC-05** | Menor | 4 | `detalle_ticket` concentra seis acciones y 185 líneas. | `views.py:182–367`; acciones en `207`, `224`, `254`, `272`, `298`, `320`. | Extraer manejadores por acción o servicios de aplicación. |
| **HC-06** | Menor | 17 | Las operaciones de múltiples escrituras no son atómicas. | `views.py:241–251`, `282–289`; `services.py:131–144`; no hay `transaction.atomic` en vistas ni servicios. | Envolver cada caso de uso en `transaction.atomic()`. |
| **HC-07** | Menor | 5 | Duplicación de lógica de destinatarios y de validación de longitud. | `services.py:63–70` vs. `75–82`; `forms.py:105` y `117`. | Extraer un helper de destinatarios y una única validación. |
| **HC-08** | Menor | 1 | Incumplimiento de PEP 8 en longitud de línea y ausencia de configuración de estilo. | 37 líneas > 79 en los cinco archivos; sin `pyproject.toml`, `setup.cfg` ni `.flake8`. | Configurar `ruff` o `flake8` y formatear el componente. |
| **HC-09** | Menor | 9 | Faltan docstrings en las vistas principales y en la lógica de despacho. | `views.py:134`, `183`, `371`; solo `446` y `465` tienen docstring. | Documentar el propósito, entradas y efectos de cada vista. |
| **HC-10** | Menor | 19 | Cobertura insuficiente de casos negativos y de la regla RF-12 completa. | `tests.py:216–230` cierra desde `Asignado`; `286–289` solo verifica que el agente quede nulo. | Agregar pruebas de transición inválida, liberación desde `En Proceso` y restricciones del admin. |
| **HC-11** | Menor | 15 | `asignar_agente` valida el rol pero no que el agente esté activo. | `services.py:126–127`; la restricción solo existe en `forms.py:96–99`. | Validar `is_active` en el servicio y probar la llamada directa. |
| **HC-12** | Menor | 20 | El modelo no impone restricciones de integridad para las reglas de negocio. | `models.py:108–133`, `245–249`: no hay `CheckConstraint`; `resolucion` admite vacío y `estado` no tiene restricción de BD. | Agregar restricciones y validaciones a nivel de modelo/migración. |
| **HC-13** | Menor | 8 | Un formulario inválido redirige y pierde los datos y los errores específicos. | `views.py:220–222`, `291–296`, `314–317`; los formularios del contexto se crean vacíos en `344–346`. | Renderizar el formulario con errores o conservar los datos mediante sesión. |
| **HC-14** | Menor | 19 | Las pruebas validan sobre todo la capa HTTP; faltan pruebas unitarias de modelo y servicio. | `Ticket.cerrar` se usa como preparación en `tests.py:233`, `244`, `256`; `asignar_agente` solo se prueba a través de la vista `271–276`. | Agregar pruebas unitarias de `Ticket.cerrar`, `asignar_agente` y `liberar_tickets_de_agente`. |

### 5.4 Detalle de los hallazgos críticos y mayores

#### HC-01 — Transiciones no autorizadas por la especificación

La especificación establece que «cualquier transición no listada aquí será rechazada por el backend» (`especificaci_n_del_proyecto.md:94`) y enumera siete transiciones (`98–106`). La implementación agrega cinco transiciones adicionales:

| Transición | Especificación §7 | `Ticket.TRANSICIONES` | Resultado |
|---|:---:|:---:|---|
| `Nuevo` → `Asignado` | ✅ | ✅ | Conforme |
| `Nuevo` → `Cancelado` | ✅ | ✅ | Conforme |
| `Asignado` → `En Proceso` | ✅ | ✅ | Conforme |
| `En Proceso` → `Resuelto` | ✅ | ✅ | Conforme |
| `Resuelto` → `Cerrado` | ✅ | ✅ | Conforme |
| `Resuelto` → `En Proceso` | ✅ | ✅ | Conforme |
| `Cerrado` → `En Proceso` | ✅ | ✅ | Conforme (reapertura) |
| `Nuevo` → `Cerrado` | ❌ | ✅ | **No conforme** |
| `Asignado` → `Cerrado` | ❌ | ✅ | **No conforme** |
| `En Proceso` → `Cerrado` | ❌ | ✅ | **No conforme** |
| `Asignado` → `Cancelado` | ❌ | ✅ | **No conforme** |
| `En Proceso` → `Cancelado` | ❌ | ✅ | **No conforme** |

**Reproducción verificada:**

```text
RF-27 Nuevo->Cerrado permitido: True
RF-27 Asignado->Cancelado permitido: True
```

**Impacto:** un agente puede cerrar un ticket `Asignado` sin pasar por `En Proceso` y `Resuelto`, lo que contradice el flujo aprobado. La interfaz muestra el botón de cierre porque `views.py:350–351` consulta la misma tabla. La prueba `tests.py:216–230` cierra desde `Asignado` y, por tanto, **consolida la desviación** en lugar de detectarla.

**Recomendación:** decidir si la especificación o el código es la fuente correcta. Si la especificación es la verdad, eliminar las cinco transiciones y agregar pruebas negativas para cada una. Si el negocio necesita cierre directo, actualizar la especificación, la matriz RBAC y las pruebas.

#### HC-04 — El panel de administración omite las reglas del dominio

El panel de Django es un punto de entrada real y no aplica las validaciones de la interfaz web:

- `TicketAdmin` no declara `readonly_fields` ni un formulario con validación: `estado`, `agente` y `resolucion` se editan libremente (`admin.py:66–81`).
- `SeguimientoInline` solo marca `fecha` como lectura; `tipo`, `usuario`, `comentario` y `es_interno` siguen editables (`admin.py:59–63`).
- `SeguimientoAdmin` no declara campos de solo lectura (`admin.py:84–87`).

**Consecuencias verificables por configuración:**

- RN-06: se puede asignar a un usuario con rol `cliente` como `agente` del ticket.
- RN-07: se puede editar un ticket `Cerrado`.
- RN-08: se puede marcar `Cerrado` sin resolución o con menos de 10 caracteres.
- RN-15: se pueden modificar o eliminar comentarios ya creados.
- RF-27: se puede cambiar `estado` a cualquier valor, sin pasar por la máquina de estados.

**Recomendación:** aplicar `readonly_fields` condicionales, limitar el queryset de `agente` a usuarios activos con rol agente, validar el cierre en un `ModelForm` del admin y hacer inmutables los seguimientos existentes.

#### HC-02 — RF-12 incompleto

`liberar_tickets_de_agente` excluye los estados finales y pone `agente = None`, pero solo cambia a `Nuevo` cuando el estado era `Asignado`:

```python
if ticket.estado == Ticket.ESTADO_ASIGNADO:
    ticket.estado = Ticket.ESTADO_NUEVO
```

**Reproducción verificada:**

```text
RF-12 tras liberar -> estado: En Proceso | agente: None
```

La especificación exige que **todos** los tickets abiertos regresen a `Nuevo` (`especificaci_n_del_proyecto.md:80`). Un ticket en `En Proceso` queda sin responsable y fuera del estado inicial, lo que dificulta su reasignación.

#### HC-03 — RN-08 no se aplica en el dominio

`CierreForm` valida la longitud (`forms.py:102–121`), pero `Ticket.cerrar()` no:

```python
def cerrar(self, resolucion):
    self.estado = self.ESTADO_CERRADO
    self.resolucion = resolucion
    self.fecha_cierre = timezone.now()
    self.save()
```

**Reproducción verificada:**

```text
RN-08 modelo -> estado: Cerrado | resolucion: 'corta' | len: 5
```

Cualquier llamada directa al modelo, un comando de gestión o el admin pueden cerrar un ticket sin la resolución mínima. La regla debe vivir en el dominio, no solo en el formulario.

#### HR-01 y HR-02 — Deuda de especificación

La especificación describe el stack y el alcance, pero no define **requerimientos no funcionales** ni **criterios de aceptación**. Esto impide verificar objetivamente aspectos como «en tiempo real», «de forma segura» o «100 % internos». Sin métricas de rendimiento, seguridad o usabilidad, la revisión de esos atributos queda a interpretación del revisor. Es la brecha documental de mayor impacto porque afecta a todos los RF.

#### HR-09 y HR-10 — Gobernanza documental y alcance de las notificaciones

El documento no tiene autor, fecha, versión, estado ni historial de cambios (`especificaci_n_del_proyecto.md:1–3`), y mezcla viñetas con tablas sin una plantilla común. Esto dificulta saber si se revisa la versión vigente y comparar cambios entre entregas. Además, la única referencia a notificaciones es «100 % internos» (`22`): no se especifica qué eventos generan aviso, quién los recibe ni cuándo. La implementación resolvió esos detalles en `REQUERIMIENTOS.md:130–143` y en `services.py`, pero esa decisión no está en la fuente de verdad, por lo que no puede verificarse contra ella.

#### HC-12 — Integridad de datos a nivel de modelo

La capa de aplicación valida varias reglas, pero la base de datos no las respalda: `Ticket.Meta` solo define orden y nombres (`models.py:130–133`), `resolucion` es `TextField(blank=True)` (`125`) y `estado` es un `CharField` sin `CheckConstraint` (`114`). Un script, una migración de datos o el admin pueden insertar un estado arbitrario o cerrar sin resolución. La validación debe existir también en el modelo o en la migración, no solo en los formularios.

#### HC-13 — Pérdida de datos en formularios inválidos

Cuando falla la validación de un comentario, un cierre o una reapertura, la vista redirige con un mensaje genérico (`views.py:220–222`, `291–296`, `314–317`) y vuelve a crear formularios vacíos (`344–346`). El usuario pierde el texto escrito y no ve qué campo falló. Es un defecto de usabilidad y de diagnóstico, no del flujo principal.

#### HC-14 — Nivel de las pruebas

Las pruebas ejercitan las reglas a través de `self.client` (`tests.py`), lo que valida la integración HTTP pero no aísla el modelo ni el servicio. `Ticket.cerrar` aparece como preparación en `233`, `244` y `256`, y `asignar_agente` solo se invoca desde la vista (`271–276`). Falta una capa de pruebas unitarias que detecte regresiones en las reglas de dominio sin depender de la vista.

### 5.5 Conformidades verificadas

La revisión también confirmó prácticas correctas que deben preservarse:

- **Autorización por objeto:** `puede_ver_ticket` impide que un cliente vea tickets ajenos y que un agente vea tickets no asignados (`decorators.py:23–29`; pruebas en `tests.py:84–97`).
- **Aislamiento de notificaciones:** `abrir_notificacion` filtra por `usuario=request.user` y devuelve 404 para notificaciones ajenas (`views.py:466–468`; `tests.py:446–454`).
- **Constantes de dominio:** estados, prioridades y categorías están centralizados, sin literales dispersos (`models.py:51–99`).
- **Uso correcto del ORM:** no hay SQL crudo y la exportación CSV usa `csv.writer`, que cita correctamente los campos (`views.py:398–427`).
- **CSRF:** middleware activo y token en los seis formularios POST de la vista de detalle (`settings.py:54`; plantilla de detalle).
- **Migraciones:** 0001–0003 aplicadas y sin cambios pendientes (`makemigrations --check` → «No changes detected»).
- **Pruebas:** 40 pruebas en verde, incluidas autorización, estados, cierre, reapertura y notificaciones.
- **Notificaciones internas:** no se envía correo electrónico; la campana y la bandeja están implementadas y probadas.

### 5.6 Observaciones de cumplimiento (fuera de las checklists)

| ID | Observación | Evidencia | Impacto |
|---|---|---|---|
| **OBS-01** | La especificación declara Django 4.2 LTS / 5.0, pero el proyecto usa Django 6.1.2. | `especificaci_n_del_proyecto.md:32`; `requirements.txt` (`Django==6.1.2`). | Desviación de stack; la versión es superior y compatible, pero debe actualizarse la especificación o fijarse la versión. |
| **OBS-02** | La especificación exige Git/GitHub o GitLab, pero el directorio no es un repositorio Git. | `especificaci_n_del_proyecto.md:35`; no existe carpeta `.git`. | Sin historial ni hash de confirmación; la trazabilidad de la revisión depende de la fecha y de los números de línea. |
| **OBS-03** | `REQUERIMIENTOS.md` explica los saltos de numeración, pero la fuente de verdad no lo hace. | `REQUERIMIENTOS.md:67`; `especificaci_n_del_proyecto.md:74–88`. | Un lector de la especificación no entiende por qué faltan identificadores. |

### 5.7 Conclusión y plan de acción

El proyecto tiene una base sólida: separación de capas, autorización por objeto, uso correcto del ORM, notificaciones internas coherentes con el alcance y una suite de 40 pruebas. Sin embargo, la revisión encontró **dos brechas críticas** entre la especificación y la implementación: la máquina de estados permite transiciones prohibidas y el panel de administración omite las reglas del dominio. Ambas son corregibles y deben atenderse antes de considerar el módulo conforme.

| Prioridad | Acción | Hallazgos | Criterio de cierre |
|---|---|---|---|
| 1 | Alinear `Ticket.TRANSICIONES` con la especificación (o actualizar la especificación y las pruebas). | HC-01 | Pruebas negativas para las cinco transiciones; `manage.py test` en verde. |
| 2 | Restringir el admin: campos de solo lectura, queryset de agentes activos y validación de cierre. | HC-04 | Prueba de admin que impide asignar cliente, editar cerrado y modificar seguimientos. |
| 3 | Corregir RF-12 para llevar todo ticket abierto a `Nuevo`. | HC-02 | Prueba con ticket `En Proceso` que verifica estado `Nuevo` y agente nulo. |
| 4 | Validar RN-08 en el modelo o servicio y respaldarla con restricciones de base de datos. | HC-03, HC-11, HC-12 | Prueba unitaria de `cerrar('corta')` que lanza error, agente inactivo rechazado y restricción de BD aplicada. |
| 5 | Agregar RNF y criterios de aceptación a la especificación. | HR-01, HR-02 | Sección de RNF con métricas y criterios por RF. |
| 6 | Unificar identificadores y crear la matriz de trazabilidad. | HR-03, HR-08 | Un ID por requisito y matriz RF ↔ código ↔ prueba. |
| 7 | Corregir referencias visuales y documentar el modelo de datos. | HR-07 | Imágenes presentes o ERD textual enlazado. |
| 8 | Refactorizar `detalle_ticket`, agregar atomicidad y eliminar duplicación. | HC-05, HC-06, HC-07 | Funciones de menos de 50 líneas, `transaction.atomic` y helper único. |
| 9 | Configurar linting y completar docstrings. | HC-08, HC-09 | `ruff`/`flake8` sin errores y docstrings en vistas públicas. |
| 10 | Ampliar la cobertura de pruebas negativas. | HC-10 | Casos inválidos cubiertos y reporte de cobertura. |
| 11 | Conservar los datos y los errores específicos cuando falla un formulario. | HC-13 | Formulario re-renderizado con errores y datos previos; prueba de usabilidad. |
| 12 | Agregar pruebas unitarias de modelo y servicio. | HC-14 | Pruebas directas de `Ticket.cerrar`, `asignar_agente` y `liberar_tickets_de_agente`. |
| 13 | Completar la gobernanza del documento y la matriz de notificaciones. | HR-04, HR-09, HR-10 | Plantilla con metadatos, glosario, control de versión y matriz evento → destinatario. |

### 5.8 Limitaciones de la revisión

- La revisión fue documental y de escritorio; no incluyó entrevistas con los autores ni una reunión formal de revisión.
- Al no existir repositorio Git, los hallazgos se ubican por archivo y línea, no por confirmación (*commit*).
- La verificación empírica se ejecutó con reversión de transacción; no se probaron cargas concurrentes ni escenarios de producción.
- Los criterios de estilo se evaluaron con PEP 8 como referencia; el equipo no tiene una guía de estilo documentada.
- No se revisaron todos los módulos del sistema, sino el componente de ciclo de vida y asignación, según el alcance declarado.

---

## 6. Referencias

- IEEE. *IEEE Standard for Software Reviews and Audits* (IEEE 1028-2008).
- ISO/IEC/IEEE. *Software and systems engineering — Work product reviews* (ISO/IEC/IEEE 20246:2017).
- Sommerville, I. *Software Engineering*. Pearson.
- Pressman, R. *Software Engineering: A Practitioner's Approach*. McGraw-Hill.
- ISTQB. *Glossary of Testing Terms* (revisión, walkthrough, inspección, revisión técnica).
- Django Software Foundation. *Django Documentation*: testing, admin, transactions, security.

---

## Apéndice A. Evidencia de ejecución

### A.1 Verificaciones del proyecto

```text
> python manage.py check
System check identified no issues (0 silenced).

> python manage.py makemigrations --check --dry-run
No changes detected

> python manage.py test
Ran 40 tests in 43.551s
OK
```

### A.2 Reproducción controlada de los hallazgos

Script ejecutado con `transaction.atomic()` y `transaction.set_rollback(True)`; los cambios no se persistieron:

```text
RF-12 tras liberar -> estado: En Proceso | agente: None
RN-08 modelo -> estado: Cerrado | resolucion: 'corta' | len: 5
RF-27 Nuevo->Cerrado permitido: True
RF-27 Asignado->Cancelado permitido: True
VERIFICACION OK (cambios revertidos)
```

### A.3 Medición de longitud de línea (PEP 8)

```text
models.py   líneas > 79: 5   máx: 94
views.py    líneas > 79: 20  máx: 97
forms.py    líneas > 79: 8   máx: 93
services.py líneas > 79: 2   máx: 92
admin.py    líneas > 79: 2   máx: 99
```

### A.4 Archivos referenciados por la especificación

```text
image_42b07a.png  -> no existe
image_42b09d.png  -> no existe
```

---

## Apéndice B. Resumen de criterios por resultado

### B.1 Requerimientos

- **Cumplen (6):** 3, 7, 8, 10, 13, 14.
- **No cumplen (14):** 1, 2, 4, 5, 6, 9, 11, 12, 15, 16, 17, 18, 19, 20.
- **No aplican (0):** ninguno.

### B.2 Código

- **Cumplen (8):** 2, 3, 6, 7, 11, 12, 14, 18.
- **No cumplen (12):** 1, 4, 5, 8, 9, 10, 13, 15, 16, 17, 19, 20.
- **No aplican (0):** ninguno.
