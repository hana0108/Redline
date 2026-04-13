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
  el('proceedSaleBtn').href = `login/index.html?vehicle_id=${encodeURIComponent(vehicle.id)}`;

  const reserveBtn = el('reserveBtn');
  const alreadyReserved = vehicle.status === 'reservado';
  reserveBtn.textContent = alreadyReserved ? 'Reservado' : 'Reservar';
  reserveBtn.disabled = alreadyReserved;
  reserveBtn.dataset.vehicleId = vehicle.id;
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

  el('reserveBtn').addEventListener('click', async () => {
    const btn = el('reserveBtn');
    const vehicleId = btn.dataset.vehicleId;
    if (!vehicleId || btn.disabled) return;
    btn.disabled = true;
    btn.textContent = 'Reservando...';
    try {
      await window.REDLINE.request(`/vehicles/public/${vehicleId}/reserve`, { method: 'POST' });
      btn.textContent = 'Reservado';
      closeModal();
      await loadVehicles();
    } catch (e) {
      btn.textContent = 'Reservar';
      btn.disabled = false;
      toast(e.message || 'No se pudo reservar el vehículo.', 'error');
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
