const state = {
  branches: [],
  vehicles: [],
};

let searchTimer;

function el(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatNumber(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return 'N/D';
  return num.toLocaleString('es-DO');
}

function toast(message, type = 'info') {
  const container = el('toastContainer');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = message;
  container.appendChild(t);
  requestAnimationFrame(() => requestAnimationFrame(() => t.classList.add('toast-visible')));
  setTimeout(() => {
    t.classList.remove('toast-visible');
    setTimeout(() => { if (t.parentNode) t.remove(); }, 300);
  }, 3800);
}

function vehicleImage(vehicle) {
  if (vehicle.image_url) {
    if (vehicle.image_url.startsWith('/')) {
      const origin = window.REDLINE.getApiOrigin();
      return origin ? `${origin}${vehicle.image_url}` : vehicle.image_url;
    }
    return vehicle.image_url;
  }
  return 'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?auto=format&fit=crop&w=1200&q=80';
}

async function loadBranches() {
  state.branches = await window.REDLINE.request('/branches/public');
  const node = el('branchFilter');
  if (!node) return;

  node.innerHTML = [
    '<option value="">Todas las sucursales</option>',
    ...state.branches.map(item => `<option value="${item.id}">${escapeHtml(item.name)}</option>`),
  ].join('');
}

const STATUS_LABELS_PUB = { reservado: 'Reservado', en_proceso: 'En proceso' };

function vehicleCard(vehicle) {
  const statusLabel = STATUS_LABELS_PUB[vehicle.status];
  const badge = statusLabel ? `<span class="badge badge--${escapeHtml(vehicle.status)}">${statusLabel}</span>` : '';
  return `
    <article class="vehicle-card" data-id="${vehicle.id}">
      <img src="${escapeHtml(vehicleImage(vehicle))}" alt="${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)}" />
      <div class="vehicle-body">
        <h4>${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)}</h4>
        ${badge}
        <p class="vehicle-price">${window.REDLINE.formatCurrencyRD(vehicle.price)}</p>
        <p class="vehicle-branch">Sucursal: ${escapeHtml(vehicle.branch_name || 'N/D')}</p>
        <div class="vehicle-meta">
          <span>${escapeHtml(vehicle.vehicle_year)}</span>
          <span>${formatNumber(vehicle.mileage)} km</span>
          <span>${escapeHtml(vehicle.transmission || 'N/D')}</span>
        </div>
      </div>
    </article>
  `;
}

function renderVehicles() {
  const grid = el('vehicleGrid');
  if (!grid) return;
  grid.innerHTML = state.vehicles.length
    ? state.vehicles.map(vehicleCard).join('')
    : '<div class="empty-state">No se encontraron vehículos para los filtros aplicados.</div>';
  el('resultCount').textContent = `${state.vehicles.length} resultados`;
}

async function loadVehicles() {
  const params = new URLSearchParams();
  const branchId = el('branchFilter').value;
  const search = el('searchInput').value.trim();
  const status = el('statusFilter').value;

  if (branchId) params.set('branch_id', branchId);
  if (search) params.set('search', search);
  if (status) params.set('status', status);

  const grid = el('vehicleGrid');
  grid.innerHTML = Array(6).fill('<div class="vehicle-skeleton"></div>').join('');
  el('resultCount').textContent = 'Cargando...';

  const path = `/vehicles/public${params.toString() ? `?${params.toString()}` : ''}`;
  try {
    state.vehicles = await window.REDLINE.request(path);
    renderVehicles();
  } catch (_) {
    grid.innerHTML = '<div class="empty-state">No se pudo cargar el inventario. Intente de nuevo.</div>';
    el('resultCount').textContent = '0 resultados';
  }
}

function fillModal(vehicle) {
  el('mImage').src = vehicleImage(vehicle);
  el('mTitle').textContent = `${vehicle.brand} ${vehicle.model}`;
  el('mPrice').textContent = window.REDLINE.formatCurrencyRD(vehicle.price);
  el('mBranch').textContent = `Sucursal: ${vehicle.branch_name || 'N/D'}`;
  el('mYear').textContent = vehicle.vehicle_year || 'N/D';
  el('mMileage').textContent = `${formatNumber(vehicle.mileage)} km`;
  el('mTransmission').textContent = vehicle.transmission || 'N/D';
  el('mFuel').textContent = vehicle.fuel_type || 'N/D';
  el('mType').textContent = vehicle.vehicle_type || 'N/D';
  el('mColor').textContent = vehicle.color || 'N/D';
  el('mDescription').textContent = vehicle.description || 'Sin descripción disponible.';

  const reserveBtn = el('reserveBtn');
  const proceedBtn = el('proceedSaleBtn');
  const alreadyReserved = vehicle.status === 'reservado';
  reserveBtn.textContent = alreadyReserved ? 'Reservado' : 'Reservar';
  reserveBtn.disabled = alreadyReserved;
  reserveBtn.dataset.vehicleId = vehicle.id;
  proceedBtn.dataset.vehicleId = vehicle.id;

  const notAvailable = vehicle.status !== 'disponible' && vehicle.status !== 'reservado';
  proceedBtn.disabled = notAvailable;
  proceedBtn.textContent = notAvailable ? 'No disponible' : 'Solicitar compra';
}

function openClientCapture(vehicleId, action) {
  el('captureVehicleId').value = vehicleId;
  el('captureAction').value = action;
  el('clientCaptureTitle').textContent = action === 'reserve' ? 'Reservar vehículo' : 'Solicitar compra';
  el('clientCaptureSubtitle').textContent = action === 'reserve'
    ? 'Ingresa tus datos para reservar este vehículo.'
    : 'Ingresa tus datos para que procesemos tu solicitud de compra.';
  el('captureFullName').value = '';
  el('capturePhone').value = '';
  el('captureEmail').value = '';
  el('captureDocType').value = '';
  el('captureDocNumber').value = '';
  el('captureNotes').value = '';
  el('captureFormError').style.display = 'none';
  el('captureSubmitBtn').disabled = false;
  el('captureSubmitBtn').textContent = 'Enviar solicitud';
  el('clientCaptureModal').style.display = 'grid';
  el('clientCaptureModal').setAttribute('aria-hidden', 'false');
}

function closeClientCapture() {
  el('clientCaptureModal').style.display = 'none';
  el('clientCaptureModal').setAttribute('aria-hidden', 'true');
}

async function submitClientCapture() {
  const vehicleId = el('captureVehicleId').value;
  const action = el('captureAction').value;
  const fullName = el('captureFullName').value.trim();
  if (!fullName) {
    el('captureFormError').textContent = 'El nombre es obligatorio.';
    el('captureFormError').style.display = 'block';
    return;
  }
  el('captureFormError').style.display = 'none';
  const btn = el('captureSubmitBtn');
  btn.disabled = true;
  btn.textContent = 'Enviando...';

  const clientPayload = {
    full_name: fullName,
    phone: el('capturePhone').value.trim() || null,
    email: el('captureEmail').value.trim() || null,
    document_type: el('captureDocType').value || null,
    document_number: el('captureDocNumber').value.trim() || null,
    notes: el('captureNotes').value.trim() || null,
  };

  const endpoint = action === 'reserve'
    ? `/vehicles/public/${vehicleId}/reserve`
    : `/vehicles/public/${vehicleId}/purchase_intent`;

  try {
    await window.REDLINE.request(endpoint, { method: 'POST', json: { client: clientPayload } });
    closeClientCapture();
    closeModal();
    await loadVehicles();
    toast(action === 'reserve'
      ? 'Vehículo reservado exitosamente. Nos pondremos en contacto contigo.'
      : 'Solicitud de compra registrada. Nos pondremos en contacto contigo.',
      'success'
    );
  } catch (e) {
    el('captureFormError').textContent = e.message || 'No se pudo procesar la solicitud.';
    el('captureFormError').style.display = 'block';
    btn.disabled = false;
    btn.textContent = 'Enviar solicitud';
  }
}

async function openVehicleModal(vehicleId) {
  try {
    const vehicle = await window.REDLINE.request(`/vehicles/public/${vehicleId}`);
    fillModal(vehicle);
    el('vehicleModal').style.display = 'grid';
    el('vehicleModal').setAttribute('aria-hidden', 'false');
  } catch (_) {
    toast('No se pudo cargar el detalle del vehículo.', 'error');
  }
}

function closeModal() {
  el('vehicleModal').style.display = 'none';
  el('vehicleModal').setAttribute('aria-hidden', 'true');
}

function wireEvents() {
  el('btnRefresh').addEventListener('click', loadVehicles);
  el('branchFilter').addEventListener('change', loadVehicles);
  el('statusFilter').addEventListener('change', loadVehicles);
  el('searchInput').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadVehicles, 250);
  });

  el('vehicleGrid').addEventListener('click', async (evt) => {
    const card = evt.target.closest('[data-id]');
    if (!card) return;
    await openVehicleModal(card.dataset.id);
  });

  el('closeModal').addEventListener('click', closeModal);
  el('vehicleModal').addEventListener('click', (evt) => {
    if (evt.target.id === 'vehicleModal') closeModal();
  });

  el('reserveBtn').addEventListener('click', () => {
    const btn = el('reserveBtn');
    const vehicleId = btn.dataset.vehicleId;
    if (!vehicleId || btn.disabled) return;
    openClientCapture(vehicleId, 'reserve');
  });

  el('proceedSaleBtn').addEventListener('click', () => {
    const btn = el('proceedSaleBtn');
    const vehicleId = btn.dataset.vehicleId;
    if (!vehicleId || btn.disabled) return;
    openClientCapture(vehicleId, 'purchase_intent');
  });

  el('closeClientCapture').addEventListener('click', closeClientCapture);
  el('clientCaptureModal').addEventListener('click', (evt) => {
    if (evt.target.id === 'clientCaptureModal') closeClientCapture();
  });
  el('captureSubmitBtn').addEventListener('click', submitClientCapture);

  document.addEventListener('keydown', (evt) => {
    if (evt.key === 'Escape') {
      if (el('clientCaptureModal').style.display !== 'none') closeClientCapture();
      else closeModal();
    }
  });
}

async function bootstrap() {
  wireEvents();
  await loadBranches();
  await loadVehicles();
}

document.addEventListener('DOMContentLoaded', () => {
  bootstrap().catch((error) => {
    const grid = el('vehicleGrid');
    if (grid) {
      grid.innerHTML = `<div class="empty-state">No se pudo cargar el inventario: ${escapeHtml(error.message || 'error desconocido')}</div>`;
    }
  });
});
