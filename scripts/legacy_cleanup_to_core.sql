-- Limpieza de una base heredada hacia el alcance core de Redline.
-- Úsalo solo si ya tienes una base vieja con leads/reservas/portal.
-- Para un entorno nuevo, prefiere reconstruir desde database/redline_schema.sql.

\set ON_ERROR_STOP on
BEGIN;

SET search_path TO redline, public;

-- Tablas fuera de alcance
DROP TABLE IF EXISTS favorites CASCADE;
DROP TABLE IF EXISTS portal_users CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;

-- Columnas fuera de alcance
ALTER TABLE IF EXISTS branches DROP COLUMN IF EXISTS is_visible_in_portal;
ALTER TABLE IF EXISTS system_settings DROP COLUMN IF EXISTS show_purchase_option;
ALTER TABLE IF EXISTS system_settings DROP COLUMN IF EXISTS show_reservation_option;
ALTER TABLE IF EXISTS vehicles DROP COLUMN IF EXISTS is_published;
ALTER TABLE IF EXISTS sales DROP COLUMN IF EXISTS reservation_id;

COMMIT;

-- Nota:
-- Si deseas eliminar también los tipos ENUM heredados o reducir valores sobrantes
-- en document_type / audit_action / vehicle_status, lo más seguro es reconstruir
-- desde cero con database/redline_schema.sql.
