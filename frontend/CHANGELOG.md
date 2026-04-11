# Historial de Cambios - Redline Selection

## [08-04-2026] - Implementación del Filtro de Búsqueda Mitiel

### Modificado
* **`index.html`**: Se actualizó la lista de marcas `<ul class="brand-list">`. Se añadió el atributo `value` a cada elemento `<input type="checkbox">` por ejemplo, `value="Toyota"` para permitir una identificación más precisa y limpia de las selecciones desde JavaScript, sin depender del texto renderizado.

### Añadido
* **`index.js`**: Se implementó la lógica funcional para el botón "BUSCAR VEHÍCULO" `.btn-sidebar-search`.
  * Se agregó un "escuchador de eventos" (Event Listener) que captura el momento en que se hace clic en el botón de búsqueda.
  * Se creó una función que recopila un array con las marcas seleccionadas por el usuario basándose en los checkboxes marcados `:checked`.
  * Se implementó un bucle que recorre todas las tarjetas del inventario `.car-card` y lee el título `<h4>` de cada vehículo.
  * Se añadió la lógica de visualización: Si el vehículo coincide con alguna de las marcas seleccionadas, se mantiene visible. Si no coincide, se oculta mediante la propiedad CSS `display: none`. Si no hay ninguna casilla marcada, se muestran todos los vehículos por defecto.