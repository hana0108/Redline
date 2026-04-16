# Backoffice Redline

Panel administrativo enfocado en el alcance actual del proyecto:

- sucursales
- vehículos
- clientes
- ventas
- configuración general

El panel permite:

- CRUD de clientes
- CRUD de vehículos
- CRUD de ventas
- carga de imágenes por archivo
- registro de imágenes por URL
- descarga de PDF de ventas

Quedaron retirados del alcance:

- SaaS / multi-dealer
- leads
- reservas
- portal público de ventas y favoritos

## Datos demo

Para cargar datos de presentación ejecutar manualmente desde el backend:

```bash
cd backend
source .deps/bin/activate
python3 -m app.db.seed_demo
```

Contraseña de usuarios demo: `Demo123*`
El proceso es idempotente y **no se ejecuta automáticamente** al iniciar la aplicación.
