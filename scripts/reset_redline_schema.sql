-- Uso: psql -U redline -d redline -f scripts/reset_redline_schema.sql
\set ON_ERROR_STOP on
BEGIN;
DROP SCHEMA IF EXISTS redline CASCADE;
COMMIT;
\i ../database/redline_schema.sql
