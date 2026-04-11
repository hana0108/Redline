# Revisión de alcance y continuidad de desarrollo - Redline

## Decisión de alcance aplicada
En el estado actual del proyecto ya quedó aplicado este enfoque:
- Sin SaaS / multi-tenant
- Sin leads
- Sin reservas
- Sin portal público de ventas
- Núcleo operativo: sucursales, clientes, vehículos, ventas, configuración y reportes
- En vehículos: subir imagen o registrar URL de imagen

## Estado actual después del recorte
### Backend
- Router limpio, sin endpoints activos de leads, reservas ni portal.
- Base ORM limpia, sin importar modelos retirados.
- Seeder de roles/permisos actualizado al nuevo alcance.
- Historial de clientes simplificado a ventas.
- Ventas desacopladas de reservas.
- Al crear una venta, el vehículo pasa a `vendido`.
- Al eliminar una venta, el vehículo vuelve a `disponible`.

### Base de datos
- Esquema canónico único actualizado a alcance core.
- Eliminadas del esquema las tablas y tipos de:
  - leads
  - reservations
  - portal_users
  - favorites
- Eliminadas columnas heredadas de portal / compra-reserva online.
- `sales` ya no incluye `reservation_id`.

### Frontend admin
- Panel reconstruido para operar solo con:
  - sucursales
  - vehículos
  - clientes
  - ventas
  - configuración
- Soporta:
  - CRUD de clientes
  - CRUD de vehículos
  - CRUD de ventas
  - imágenes por archivo
  - imágenes por URL
  - PDF de ventas

### Frontend público
- Quedó desactivado como parte del alcance. La página principal ahora muestra una nota de retiro del portal público.

## Validaciones ejecutadas
- Sintaxis Python validada con `python -m compileall app`
- Sintaxis JavaScript validada con `node --check`

## Pendientes recomendados
1. Probar flujo completo con PostgreSQL real:
   - crear sucursal
   - crear cliente
   - crear vehículo
   - subir imagen / URL
   - registrar venta
   - editar venta
   - eliminar venta
2. Crear una migración SQL específica si vas a actualizar una base ya existente con datos heredados.
3. Agregar pruebas automáticas mínimas para ventas, clientes y vehículos.
