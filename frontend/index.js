document.addEventListener('DOMContentLoaded', () => {
  const msg = document.getElementById('retiredMessage');
  const base = document.getElementById('apiBaseLabel');
  if (base) base.textContent = window.REDLINE.getApiBase();
  if (msg) {
    msg.textContent = 'El portal público fue retirado de este alcance. Usa el backoffice para gestionar clientes, vehículos y ventas.';
  }
  const btn = document.getElementById('btnSaveApi');
  if (btn) {
    btn.addEventListener('click', () => {
      const val = document.getElementById('apiBaseInput')?.value?.trim();
      if (!val) return;
      window.REDLINE.setApiBase(val);
      if (base) base.textContent = window.REDLINE.getApiBase();
    });
  }
});
