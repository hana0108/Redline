function el(id) { return document.getElementById(id); }

let CURRENT_USER = null;
let BRANCHES = [];
let USERS = [];
let VEHICLES = [];
let CLIENTS = [];
let SALES = [];
let CATALOGS = { brands: [], vehicle_types: [], fuel_types: [], transmissions: [], colors: [] };
let VEHICLE_MODELS = [];
let ACTIVE_IMAGES_VEHICLE_ID = null;

const STATUS_LABELS = {
  disponible: 'Disponible',
  reservado: 'Reservado',
  vendido: 'Vendido',
  en_proceso: 'En proceso',
  retirado: 'Retirado',
};

const SALE_LABELS = {
  completada: 'Completada',
  anulada: 'Anulada',
};

function ensureAuthenticated() {
  if (!window.REDLINE.getToken()) {
    window.location.href = '../login/index.html';
    return false;
  }
  return true;
}

function setText(id, value) {
  const node = el(id);
  if (node) node.textContent = value;
}

function showMessage(id, message, isError = false) {
  const node = el(id);
  if (!node) return;
  node.textContent = message || '';
  node.style.color = isError ? '#b11b17' : '#67717c';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDateTime(value) {
  if (!value) return 'N/D';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('es-DO');
}

function toDatetimeLocalInput(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function toISOFromInput(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function badgeClass(kind) {
  if (['disponible', 'completada'].includes(kind)) return 'available';
  if (['reservado', 'en_proceso'].includes(kind)) return 'warning';
  if (['vendido'].includes(kind)) return 'info';
  return 'other';
}

function askConfirmation(message) {
  return window.confirm(message);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function downloadApiFile(path, filename) {
  const blob = await window.REDLINE.request(path, { responseType: 'blob' });
  downloadBlob(blob, filename);
}

function optionHtml(value, label, selected = false) {
  return `<option value="${escapeHtml(value)}" ${selected ? 'selected' : ''}>${escapeHtml(label)}</option>`;
}

function populateSelect(id, items, placeholder, selectedValue = '', mapper = (x) => ({ value: x.id, label: x.name || x.full_name || x.id })) {
  const node = el(id);
  if (!node) return;
  const options = [`<option value="">${escapeHtml(placeholder)}</option>`]
    .concat(items.map(item => {
      const mapped = mapper(item);
      return optionHtml(mapped.value, mapped.label, String(mapped.value) === String(selectedValue));
    }));
  node.innerHTML = options.join('');
}

function populateCatalogSelect(id, items, placeholder, selectedValue = '') {
  const node = el(id);
  if (!node) return;
  node.innerHTML = [
    `<option value="">${escapeHtml(placeholder)}</option>`,
    ...items.map(item =>
      `<option value="${escapeHtml(item.name)}"${item.name === selectedValue ? ' selected' : ''}>${escapeHtml(item.name)}</option>`
    ),
  ].join('');
}

async function loadVehicleModels(brandName, selectedModel = '') {
  if (!brandName) {
    populateCatalogSelect('vehicleModel', [], 'Modelo');
    VEHICLE_MODELS = [];
    return;
  }
  try {
    const models = await window.REDLINE.request(
      `/catalogs/vehicle-models?brand_code=${encodeURIComponent(brandName)}`
    );
    VEHICLE_MODELS = models;
    populateCatalogSelect('vehicleModel', models, 'Modelo', selectedModel);
  } catch (_) {
    populateCatalogSelect('vehicleModel', [], 'Modelo');
    VEHICLE_MODELS = [];
  }
}

function syncCatalogSelects() {
  populateCatalogSelect('vehicleBrand', CATALOGS.brands || [], 'Marca');
  populateCatalogSelect('vehicleColor', CATALOGS.colors || [], 'Color');
  populateCatalogSelect('vehicleTransmission', CATALOGS.transmissions || [], 'Transmisión');
  populateCatalogSelect('vehicleFuelType', CATALOGS.fuel_types || [], 'Combustible');
  populateCatalogSelect('vehicleType', CATALOGS.vehicle_types || [], 'Tipo de vehículo');

  // Client preference selects reuse the same catalog data — preserve current selection
  const savedColor = el('prefColor')?.value || '';
  const savedTrans = el('prefTransmission')?.value || '';
  const savedFuel = el('prefFuelType')?.value || '';
  const savedType = el('prefVehicleType')?.value || '';
  populateCatalogSelect('prefColor', CATALOGS.colors || [], 'Color', savedColor);
  populateCatalogSelect('prefTransmission', CATALOGS.transmissions || [], 'Transmisión', savedTrans);
  populateCatalogSelect('prefFuelType', CATALOGS.fuel_types || [], 'Combustible', savedFuel);
  populateCatalogSelect('prefVehicleType', CATALOGS.vehicle_types || [], 'Tipo de vehículo', savedType);
}

async function loadCatalogs() {
  try {
    CATALOGS = await window.REDLINE.request('/catalogs/vehicles');
  } catch (_) {
    // Catalogs are non-critical; keep empty defaults
  }
  syncCatalogSelects();
}

function getUserName(userId) {
  return USERS.find(user => user.id === userId)?.full_name || 'Sin asignar';
}

function getBranchName(branchId) {
  return BRANCHES.find(branch => branch.id === branchId)?.name || 'Sin sucursal';
}

function getClientName(clientId) {
  return CLIENTS.find(client => client.id === clientId)?.full_name || 'Cliente desconocido';
}

function getVehicleLabel(vehicleId) {
  const vehicle = VEHICLES.find(item => item.id === vehicleId);
  return vehicle ? `${vehicle.brand} ${vehicle.model} · ${vehicle.vin}` : 'Vehículo desconocido';
}

function activeOrRelevantVehicles(branchId = null) {
  return VEHICLES.filter(v =>
    v.status !== 'vendido' &&
    v.status !== 'retirado' &&
    (!branchId || String(v.branch_id) === String(branchId))
  );
}

function syncSharedSelects() {
  const branchMapper = (item) => ({ value: item.id, label: item.name });
  populateSelect('vehicleBranch', BRANCHES, BRANCHES.length ? 'Selecciona sucursal' : 'Primero crea una sucursal', el('vehicleBranch')?.value, branchMapper);
  populateSelect('saleBranch', BRANCHES, BRANCHES.length ? 'Sucursal' : 'Sin sucursales', el('saleBranch')?.value, branchMapper);

  const clientMapper = (item) => ({ value: item.id, label: item.full_name });
  populateSelect('saleClient', CLIENTS, CLIENTS.length ? 'Selecciona cliente' : 'Sin clientes', el('saleClient')?.value, clientMapper);

  const vehicleMapper = (item) => ({ value: item.id, label: `${item.brand} ${item.model} · ${item.vin}` });
  const selectedBranch = el('saleBranch')?.value || null;
  const branchVehicles = activeOrRelevantVehicles(selectedBranch);
  populateSelect('saleVehicle', branchVehicles, branchVehicles.length ? 'Selecciona vehículo' : 'Sin vehículos en esta sucursal', el('saleVehicle')?.value, vehicleMapper);

  const userMapper = (item) => ({ value: item.id, label: `${item.full_name} · ${item.role?.name || item.role}` });
  populateSelect('saleSeller', USERS, 'Sin vendedor', el('saleSeller')?.value, userMapper);
}

async function loadCurrentUser() {
  const me = await window.REDLINE.request('/auth/me');
  CURRENT_USER = me;
  setText('welcomeText', `${me.full_name} · ${me.role} · ${me.email}`);
  setText('metricPermissions', String((me.permissions || []).length));
}

async function loadUsers() {
  try {
    USERS = await window.REDLINE.request('/users');
  } catch (error) {
    if (error.status === 403) {
      USERS = CURRENT_USER ? [{ id: CURRENT_USER.id, full_name: CURRENT_USER.full_name, role: CURRENT_USER.role, email: CURRENT_USER.email }] : [];
      return;
    }
    throw error;
  }
}

async function loadBranches() {
  BRANCHES = await window.REDLINE.request('/branches');
  setText('metricBranches', String(BRANCHES.length));

  el('branchList').innerHTML = BRANCHES.length
    ? BRANCHES.map(branch => `
      <div class="list-item">
        <strong>${escapeHtml(branch.name)}</strong>
        <div class="muted">${escapeHtml(branch.address || 'Sin dirección')} · ${escapeHtml(branch.phone || 'Sin teléfono')}</div>
        <div class="muted">Estado: ${escapeHtml(branch.status)}</div>
      </div>
    `).join('')
    : '<div class="muted">No hay sucursales registradas todavía.</div>';

  syncSharedSelects();
}

function vehicleCard(vehicle) {
  const img = window.REDLINE.pickCoverImage(vehicle) || 'https://via.placeholder.com/800x450?text=Sin+imagen';
  return `
    <article class="vehicle-card">
      <img src="${escapeHtml(img)}" alt="${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)}" />
      <div>
        <div class="entity-card-header">
          <div>
            <h4>${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)}</h4>
            <div class="muted">VIN: ${escapeHtml(vehicle.vin)} · Placa: ${escapeHtml(vehicle.plate || 'N/D')} · ${escapeHtml(getBranchName(vehicle.branch_id))}</div>
          </div>
          <div class="entity-actions">
            <span class="badge ${badgeClass(vehicle.status)}">${escapeHtml(STATUS_LABELS[vehicle.status] || vehicle.status)}</span>
          </div>
        </div>
        <div class="meta-grid">
          <div class="meta-pill">Año: ${vehicle.vehicle_year}</div>
          <div class="meta-pill">Precio: ${window.REDLINE.formatCurrencyRD(vehicle.price)}</div>
          <div class="meta-pill">Millaje: ${vehicle.mileage || 0}</div>
          <div class="meta-pill">Color: ${escapeHtml(vehicle.color || 'N/D')}</div>
          <div class="meta-pill">Transmisión: ${escapeHtml(vehicle.transmission || 'N/D')}</div>
          <div class="meta-pill">Combustible: ${escapeHtml(vehicle.fuel_type || 'N/D')}</div>
        </div>
        <p class="muted">${escapeHtml(vehicle.description || 'Sin descripción.')}</p>
        <div class="vehicle-actions">
          <button class="btn secondary small" data-action="edit-vehicle" data-id="${vehicle.id}">Editar</button>
          <button class="btn secondary small" data-action="images" data-id="${vehicle.id}">Imágenes</button>
          <button class="btn danger small" data-action="delete-vehicle" data-id="${vehicle.id}">Eliminar</button>
          <select class="status-select" data-action="status" data-id="${vehicle.id}">
            ${Object.entries(STATUS_LABELS).map(([value, label]) => `<option value="${value}" ${vehicle.status === value ? 'selected' : ''}>${label}</option>`).join('')}
          </select>
        </div>
      </div>
    </article>
  `;
}

function renderVehicles() {
  const search = el('vehicleSearch').value.trim().toLowerCase();
  const status = el('vehicleStatusFilter').value;
  const filtered = VEHICLES.filter(vehicle => {
    const text = `${vehicle.brand} ${vehicle.model} ${vehicle.vin} ${vehicle.plate || ''}`.toLowerCase();
    return (!search || text.includes(search)) && (!status || vehicle.status === status);
  });

  setText('metricVehicles', String(VEHICLES.length));
  el('vehicleList').innerHTML = filtered.length
    ? filtered.map(vehicleCard).join('')
    : '<div class="muted">No hay vehículos que coincidan con el filtro.</div>';
}

async function loadVehicles() {
  VEHICLES = await window.REDLINE.request('/vehicles');
  renderVehicles();
  syncSharedSelects();
}

function resetVehicleForm() {
  el('vehicleForm').reset();
  el('vehicleId').value = '';
  if (BRANCHES[0]) el('vehicleBranch').value = BRANCHES[0].id;
  showMessage('vehicleFormStatus', '');
}

function fillVehicleForm(vehicle) {
  el('vehicleId').value = vehicle.id;
  el('vehicleBranch').value = vehicle.branch_id;
  el('vehicleVin').value = vehicle.vin;
  el('vehicleBrand').value = vehicle.brand;
  // Load models for this brand, then set the model value
  loadVehicleModels(vehicle.brand, vehicle.model).catch(() => {
    const node = el('vehicleModel');
    if (node) node.innerHTML = `<option value="${escapeHtml(vehicle.model || '')}">${escapeHtml(vehicle.model || 'Modelo')}</option>`;
  });
  el('vehicleYear').value = vehicle.vehicle_year;
  el('vehiclePrice').value = vehicle.price;
  el('vehicleMileage').value = vehicle.mileage || 0;
  el('vehiclePlate').value = vehicle.plate || '';
  el('vehicleColor').value = vehicle.color || '';
  el('vehicleTransmission').value = vehicle.transmission || '';
  el('vehicleFuelType').value = vehicle.fuel_type || '';
  el('vehicleType').value = vehicle.vehicle_type || '';
  el('vehicleDescription').value = vehicle.description || '';
  window.scrollTo({ top: el('sectionVehicles').offsetTop - 20, behavior: 'smooth' });
  showMessage('vehicleFormStatus', `Editando ${vehicle.brand} ${vehicle.model}`);
}

function collectVehiclePayload() {
  return {
    branch_id: el('vehicleBranch').value,
    vin: el('vehicleVin').value.trim(),
    brand: el('vehicleBrand').value,
    model: el('vehicleModel').value,
    vehicle_year: Number(el('vehicleYear').value),
    price: Number(el('vehiclePrice').value),
    mileage: Number(el('vehicleMileage').value || 0),
    plate: el('vehiclePlate').value.trim() || null,
    color: el('vehicleColor').value || null,
    transmission: el('vehicleTransmission').value || null,
    fuel_type: el('vehicleFuelType').value || null,
    vehicle_type: el('vehicleType').value || null,
    description: el('vehicleDescription').value.trim() || null,
  };
}

function collectClientPreference() {
  const brands = el('prefBrands').value.split(',').map(item => item.trim()).filter(Boolean);
  const payload = {
    preferred_brands: brands.length ? brands : null,
    price_min: el('prefPriceMin').value ? Number(el('prefPriceMin').value) : null,
    price_max: el('prefPriceMax').value ? Number(el('prefPriceMax').value) : null,
    vehicle_type: el('prefVehicleType').value || null,
    transmission: el('prefTransmission').value || null,
    fuel_type: el('prefFuelType').value || null,
    color: el('prefColor').value || null,
    notes: el('prefNotes').value.trim() || null,
  };
  return Object.values(payload).some(value => Array.isArray(value) ? value.length : value !== null && value !== '') ? payload : null;
}

function resetClientForm() {
  el('clientForm').reset();
  el('clientId').value = '';
  showMessage('clientFormStatus', '');
}

function fillClientForm(client) {
  el('clientId').value = client.id;
  el('clientFullName').value = client.full_name || '';
  el('clientDocumentType').value = client.document_type || '';
  el('clientDocumentNumber').value = client.document_number || '';
  el('clientEmail').value = client.email || '';
  el('clientPhone').value = client.phone || '';
  el('clientAlternatePhone').value = client.alternate_phone || '';
  el('clientAddress').value = client.address || '';
  el('clientNotes').value = client.notes || '';
  el('prefBrands').value = (client.preference?.preferred_brands || []).join(', ');
  el('prefVehicleType').value = client.preference?.vehicle_type || '';
  el('prefTransmission').value = client.preference?.transmission || '';
  el('prefFuelType').value = client.preference?.fuel_type || '';
  el('prefColor').value = client.preference?.color || '';
  el('prefPriceMin').value = client.preference?.price_min ?? '';
  el('prefPriceMax').value = client.preference?.price_max ?? '';
  el('prefNotes').value = client.preference?.notes || '';
  window.scrollTo({ top: el('sectionClients').offsetTop - 20, behavior: 'smooth' });
  showMessage('clientFormStatus', `Editando cliente ${client.full_name}`);
}

function clientCard(client) {
  const preferenceBrands = client.preference?.preferred_brands?.join(', ') || 'Sin marcas definidas';
  return `
    <div class="entity-card">
      <div class="entity-card-header">
        <div>
          <h4>${escapeHtml(client.full_name)}</h4>
          <div class="muted">${escapeHtml(client.email || 'Sin email')} · ${escapeHtml(client.phone || 'Sin teléfono')}</div>
        </div>
        <span class="badge info">Cliente</span>
      </div>
      <div class="entity-meta">
        <span class="meta-pill">Documento: ${escapeHtml(client.document_type || 'N/D')} ${escapeHtml(client.document_number || '')}</span>
        <span class="meta-pill">Preferencias: ${escapeHtml(preferenceBrands)}</span>
      </div>
      <div class="muted">${escapeHtml(client.address || 'Sin dirección')} · Creado: ${formatDateTime(client.created_at)}</div>
      <div class="entity-actions" style="margin-top: 12px;">
        <button class="btn secondary small" data-action="edit-client" data-id="${client.id}">Editar</button>
        <button class="btn secondary small" data-action="history-client" data-id="${client.id}">Historial</button>
        <button class="btn danger small" data-action="delete-client" data-id="${client.id}">Eliminar</button>
      </div>
    </div>
  `;
}

function renderClients() {
  const search = el('clientSearch').value.trim().toLowerCase();
  const filtered = CLIENTS.filter(client => {
    const text = `${client.full_name} ${client.email || ''} ${client.phone || ''} ${client.document_number || ''}`.toLowerCase();
    return !search || text.includes(search);
  });
  setText('metricClients', String(CLIENTS.length));
  el('clientList').innerHTML = filtered.length ? filtered.map(clientCard).join('') : '<div class="muted">No hay clientes para mostrar.</div>';
}

async function loadClients() {
  const search = el('clientSearch')?.value.trim();
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  CLIENTS = await window.REDLINE.request(`/clients${query}`);
  renderClients();
  syncSharedSelects();
}

function showClientHistory(history, clientId) {
  const panel = el('clientHistoryPanel');
  const client = CLIENTS.find(item => item.id === clientId);
  panel.classList.remove('hidden');
  panel.innerHTML = `
    <div class="card-head space-between">
      <div>
        <h3>Historial de ${escapeHtml(client?.full_name || 'cliente')}</h3>
        <span class="muted">Ventas relacionadas</span>
      </div>
      <button class="btn secondary small" id="closeClientHistoryBtn">Cerrar</button>
    </div>
    <div class="history-grid">
      <div class="history-box">
        <h5>Ventas (${history.sales.length})</h5>
        ${history.sales.length ? `<ul>${history.sales.map(item => `<li>${escapeHtml(getVehicleLabel(item.vehicle_id))} · ${window.REDLINE.formatCurrencyRD(item.sale_price)} · ${formatDateTime(item.sale_date)}</li>`).join('')}</ul>` : '<div class="muted">Sin ventas.</div>'}
      </div>
    </div>
  `;
  el('closeClientHistoryBtn').addEventListener('click', () => panel.classList.add('hidden'));
}

function saleCard(item) {
  return `
    <div class="entity-card">
      <div class="entity-card-header">
        <div>
          <h4>${escapeHtml(getClientName(item.client_id))}</h4>
          <div class="muted">${escapeHtml(getVehicleLabel(item.vehicle_id))}</div>
        </div>
        <span class="badge ${badgeClass(item.status)}">${escapeHtml(SALE_LABELS[item.status] || item.status)}</span>
      </div>
      <div class="entity-meta">
        <span class="meta-pill">Sucursal: ${escapeHtml(getBranchName(item.branch_id))}</span>
        <span class="meta-pill">Vendedor: ${escapeHtml(item.seller_user_id ? getUserName(item.seller_user_id) : 'Sin vendedor')}</span>
        <span class="meta-pill">Pago: ${escapeHtml(item.payment_method || 'No indicado')}</span>
      </div>
      <div class="muted">Fecha: ${formatDateTime(item.sale_date)} · Precio: ${window.REDLINE.formatCurrencyRD(item.sale_price)}</div>
      <div class="entity-actions" style="margin-top: 12px;">
        <button class="btn secondary small" data-action="edit-sale" data-id="${item.id}">Editar</button>
        <button class="btn secondary small" data-action="pdf-sale" data-id="${item.id}">PDF</button>
        <button class="btn danger small" data-action="delete-sale" data-id="${item.id}">Eliminar</button>
      </div>
    </div>
  `;
}

function renderSales() {
  setText('metricSales', String(SALES.length));
  el('saleList').innerHTML = SALES.length ? SALES.map(saleCard).join('') : '<div class="muted">No hay ventas registradas.</div>';
}

async function loadSales() {
  SALES = await window.REDLINE.request('/sales');
  renderSales();
}

function resetSaleForm() {
  el('saleForm').reset();
  el('saleId').value = '';
  if (BRANCHES[0]) el('saleBranch').value = BRANCHES[0].id;
  el('saleDate').value = '';
  showMessage('saleFormStatus', '');
  syncSharedSelects();
}

function fillSaleForm(sale) {
  el('saleId').value = sale.id;
  el('saleBranch').value = sale.branch_id;
  syncSharedSelects();
  el('saleClient').value = sale.client_id;
  el('saleVehicle').value = sale.vehicle_id;
  el('saleSeller').value = sale.seller_user_id || '';
  el('saleDate').value = toDatetimeLocalInput(sale.sale_date);
  el('salePrice').value = sale.sale_price;
  el('saleCost').value = sale.cost ?? '';
  el('salePaymentMethod').value = sale.payment_method || '';
  el('saleNotes').value = sale.notes || '';
  window.scrollTo({ top: el('sectionSales').offsetTop - 20, behavior: 'smooth' });
  showMessage('saleFormStatus', `Editando venta ${sale.id}`);
}

function fillSettingsForm(settings) {
  el('settingsBusinessName').value = settings.business_name || '';
  el('settingsLogoPath').value = settings.logo_path || '';
  el('settingsContactEmail').value = settings.contact_email || '';
  el('settingsContactPhone').value = settings.contact_phone || '';
  el('settingsWhatsapp').value = settings.whatsapp || '';
  el('settingsAddress').value = settings.address || '';
  el('settingsFacebook').value = settings.facebook || '';
  el('settingsInstagram').value = settings.instagram || '';
  el('settingsWebsite').value = settings.website || '';
  el('settingsTerms').value = settings.terms_and_conditions || '';
  el('settingsPrivacy').value = settings.privacy_policy || '';
}

async function loadSettings() {
  const settings = await window.REDLINE.request('/settings');
  fillSettingsForm(settings);
}

async function refreshImages() {
  if (!ACTIVE_IMAGES_VEHICLE_ID) return;
  const images = await window.REDLINE.request(`/vehicles/${ACTIVE_IMAGES_VEHICLE_ID}/images`);
  el('imagesList').innerHTML = images.length ? images.map(image => `
    <div class="image-card">
      <img src="${escapeHtml(window.REDLINE.pickCoverImage({ images: [image] }) || image.file_path)}" alt="Imagen" />
      <div class="muted">Orden: ${image.sort_order} ${image.is_cover ? '· Portada' : ''}</div>
      <div class="entity-actions">
        <button class="btn secondary small" data-image-action="cover" data-image-id="${image.id}">Portada</button>
        <button class="btn danger small" data-image-action="delete" data-image-id="${image.id}">Eliminar</button>
      </div>
    </div>
  `).join('') : '<div class="muted">Sin imágenes.</div>';
}

async function openImagesPanel(vehicle) {
  ACTIVE_IMAGES_VEHICLE_ID = vehicle.id;
  el('imagesPanel').classList.remove('hidden');
  setText('imagesTitle', `${vehicle.brand} ${vehicle.model} · ${vehicle.vin}`);
  el('imagesPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  await refreshImages();
}

async function handleBranchSubmit(evt) {
  evt.preventDefault();
  const payload = {
    name: el('branchName').value.trim(),
    phone: el('branchPhone').value.trim() || null,
    email: el('branchEmail').value.trim() || null,
    address: el('branchAddress').value.trim() || null,
  };
  showMessage('branchFormStatus', 'Guardando sucursal...');
  try {
    await window.REDLINE.request('/branches', { method: 'POST', json: payload });
    el('branchForm').reset();
    showMessage('branchFormStatus', 'Sucursal creada correctamente.');
    await loadBranches();
  } catch (error) {
    showMessage('branchFormStatus', error.message, true);
  }
}

async function handleVehicleSubmit(evt) {
  evt.preventDefault();
  const vehicleId = el('vehicleId').value;
  const payload = collectVehiclePayload();
  showMessage('vehicleFormStatus', vehicleId ? 'Actualizando vehículo...' : 'Creando vehículo...');
  try {
    if (vehicleId) {
      await window.REDLINE.request(`/vehicles/${vehicleId}`, { method: 'PATCH', json: payload });
      showMessage('vehicleFormStatus', 'Vehículo actualizado correctamente.');
    } else {
      await window.REDLINE.request('/vehicles', { method: 'POST', json: payload });
      showMessage('vehicleFormStatus', 'Vehículo creado correctamente.');
    }
    resetVehicleForm();
    await loadVehicles();
  } catch (error) {
    showMessage('vehicleFormStatus', error.message, true);
  }
}

async function handleClientSubmit(evt) {
  evt.preventDefault();
  const clientId = el('clientId').value;
  const payload = {
    full_name: el('clientFullName').value.trim(),
    document_type: el('clientDocumentType').value.trim() || null,
    document_number: el('clientDocumentNumber').value.trim() || null,
    email: el('clientEmail').value.trim() || null,
    phone: el('clientPhone').value.trim() || null,
    alternate_phone: el('clientAlternatePhone').value.trim() || null,
    address: el('clientAddress').value.trim() || null,
    notes: el('clientNotes').value.trim() || null,
    preference: collectClientPreference(),
  };
  showMessage('clientFormStatus', clientId ? 'Actualizando cliente...' : 'Creando cliente...');
  try {
    if (clientId) {
      await window.REDLINE.request(`/clients/${clientId}`, { method: 'PATCH', json: payload });
      showMessage('clientFormStatus', 'Cliente actualizado correctamente.');
    } else {
      await window.REDLINE.request('/clients', { method: 'POST', json: payload });
      showMessage('clientFormStatus', 'Cliente creado correctamente.');
    }
    resetClientForm();
    await loadClients();
  } catch (error) {
    showMessage('clientFormStatus', error.message, true);
  }
}

async function handleSaleSubmit(evt) {
  evt.preventDefault();
  const saleId = el('saleId').value;
  const payload = {
    branch_id: el('saleBranch').value,
    client_id: el('saleClient').value,
    vehicle_id: el('saleVehicle').value,
    seller_user_id: el('saleSeller').value || null,
    sale_date: toISOFromInput(el('saleDate').value),
    sale_price: Number(el('salePrice').value),
    cost: el('saleCost').value ? Number(el('saleCost').value) : null,
    payment_method: el('salePaymentMethod').value.trim() || null,
    notes: el('saleNotes').value.trim() || null,
  };
  if (!payload.sale_date) delete payload.sale_date;
  showMessage('saleFormStatus', saleId ? 'Actualizando venta...' : 'Creando venta...');
  try {
    if (saleId) {
      await window.REDLINE.request(`/sales/${saleId}`, { method: 'PATCH', json: payload });
      showMessage('saleFormStatus', 'Venta actualizada correctamente.');
    } else {
      await window.REDLINE.request('/sales', { method: 'POST', json: payload });
      showMessage('saleFormStatus', 'Venta registrada correctamente.');
    }
    resetSaleForm();
    await Promise.all([loadSales(), loadVehicles(), loadClients()]);
  } catch (error) {
    showMessage('saleFormStatus', error.message, true);
  }
}

async function handleSettingsSubmit(evt) {
  evt.preventDefault();
  const payload = {
    business_name: el('settingsBusinessName').value.trim(),
    logo_path: el('settingsLogoPath').value.trim() || null,
    contact_email: el('settingsContactEmail').value.trim() || null,
    contact_phone: el('settingsContactPhone').value.trim() || null,
    whatsapp: el('settingsWhatsapp').value.trim() || null,
    address: el('settingsAddress').value.trim() || null,
    facebook: el('settingsFacebook').value.trim() || null,
    instagram: el('settingsInstagram').value.trim() || null,
    website: el('settingsWebsite').value.trim() || null,
    terms_and_conditions: el('settingsTerms').value.trim() || null,
    privacy_policy: el('settingsPrivacy').value.trim() || null,
  };
  showMessage('settingsFormStatus', 'Guardando configuración...');
  try {
    const saved = await window.REDLINE.request('/settings', { method: 'PATCH', json: payload });
    fillSettingsForm(saved);
    showMessage('settingsFormStatus', 'Configuración actualizada correctamente.');
  } catch (error) {
    showMessage('settingsFormStatus', error.message, true);
  }
}

async function handleImageSubmit(evt) {
  evt.preventDefault();
  if (!ACTIVE_IMAGES_VEHICLE_ID) return;
  const file = el('imageFile').files?.[0];
  if (!file) {
    showMessage('imageUploadStatus', 'Selecciona una imagen.', true);
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  formData.append('sort_order', el('imageSortOrder').value || '0');
  formData.append('is_cover', String(el('imageIsCover').checked));
  showMessage('imageUploadStatus', 'Subiendo imagen...');
  try {
    await window.REDLINE.request(`/vehicles/${ACTIVE_IMAGES_VEHICLE_ID}/images/upload`, { method: 'POST', body: formData });
    el('imageUploadForm').reset();
    el('imageSortOrder').value = '0';
    showMessage('imageUploadStatus', 'Imagen subida correctamente.');
    await refreshImages();
    await loadVehicles();
  } catch (error) {
    showMessage('imageUploadStatus', error.message, true);
  }
}

async function handleImageUrlSubmit(evt) {
  evt.preventDefault();
  if (!ACTIVE_IMAGES_VEHICLE_ID) return;
  const imageUrl = el('imageUrl').value.trim();
  if (!imageUrl) {
    showMessage('imageUploadStatus', 'Indica una URL de imagen válida.', true);
    return;
  }

  showMessage('imageUploadStatus', 'Guardando URL de imagen...');
  try {
    await window.REDLINE.request(`/vehicles/${ACTIVE_IMAGES_VEHICLE_ID}/images`, {
      method: 'POST',
      json: {
        file_path: imageUrl,
        sort_order: Number(el('imageUrlSortOrder').value || 0),
        is_cover: el('imageUrlIsCover').checked,
      },
    });
    el('imageUrlForm').reset();
    el('imageUrlSortOrder').value = '0';
    showMessage('imageUploadStatus', 'URL de imagen guardada correctamente.');
    await refreshImages();
    await loadVehicles();
  } catch (error) {
    showMessage('imageUploadStatus', error.message, true);
  }
}

async function handleMainClick(evt) {
  const button = evt.target.closest('[data-action]');
  if (!button) return;
  const action = button.dataset.action;
  const id = button.dataset.id;
  try {
    if (action === 'edit-vehicle') {
      const vehicle = VEHICLES.find(item => item.id === id);
      if (vehicle) fillVehicleForm(vehicle);
      return;
    }
    if (action === 'images') {
      const vehicle = VEHICLES.find(item => item.id === id);
      if (vehicle) await openImagesPanel(vehicle);
      return;
    }
    if (action === 'delete-vehicle') {
      if (!askConfirmation('¿Eliminar este vehículo?')) return;
      await window.REDLINE.request(`/vehicles/${id}`, { method: 'DELETE' });
      await loadVehicles();
      return;
    }
    if (action === 'edit-client') {
      const client = CLIENTS.find(item => item.id === id);
      if (client) fillClientForm(client);
      return;
    }
    if (action === 'history-client') {
      const history = await window.REDLINE.request(`/clients/${id}/history`);
      showClientHistory(history, id);
      return;
    }
    if (action === 'delete-client') {
      if (!askConfirmation('¿Eliminar este cliente?')) return;
      await window.REDLINE.request(`/clients/${id}`, { method: 'DELETE' });
      await Promise.all([loadClients(), loadSales()]);
      return;
    }
    if (action === 'pdf-sale') {
      await downloadApiFile(`/sales/${id}/pdf`, `venta_${id}.pdf`);
      return;
    }
    if (action === 'edit-sale') {
      const sale = SALES.find(item => item.id === id);
      if (sale) fillSaleForm(sale);
      return;
    }
    if (action === 'delete-sale') {
      if (!askConfirmation('¿Eliminar esta venta? El vehículo volverá a estar disponible.')) return;
      await window.REDLINE.request(`/sales/${id}`, { method: 'DELETE' });
      await Promise.all([loadVehicles(), loadSales()]);
      return;
    }
  } catch (error) {
    alert(error.message);
  }
}

async function handleMainChange(evt) {
  const target = evt.target;
  const action = target?.dataset?.action;
  if (!action) return;
  try {
    if (action === 'status') {
      await window.REDLINE.request(`/vehicles/${target.dataset.id}/status`, { method: 'PATCH', json: { status: target.value, notes: null } });
      await loadVehicles();
      return;
    }
  } catch (error) {
    alert(error.message);
  }
}

async function handleImageActions(evt) {
  const button = evt.target.closest('[data-image-action]');
  if (!button || !ACTIVE_IMAGES_VEHICLE_ID) return;
  try {
    if (button.dataset.imageAction === 'cover') {
      await window.REDLINE.request(`/vehicles/${ACTIVE_IMAGES_VEHICLE_ID}/images/${button.dataset.imageId}/cover`, { method: 'PATCH' });
    }
    if (button.dataset.imageAction === 'delete') {
      await window.REDLINE.request(`/vehicles/${ACTIVE_IMAGES_VEHICLE_ID}/images/${button.dataset.imageId}`, { method: 'DELETE' });
    }
    await refreshImages();
    await loadVehicles();
  } catch (error) {
    showMessage('imageUploadStatus', error.message, true);
  }
}

function wireUi() {
  el('logoutBtn').addEventListener('click', () => {
    window.REDLINE.clearToken();
    window.location.href = '../login/index.html';
  });

  el('branchForm').addEventListener('submit', handleBranchSubmit);
  el('vehicleForm').addEventListener('submit', handleVehicleSubmit);
  el('clientForm').addEventListener('submit', handleClientSubmit);
  el('saleForm').addEventListener('submit', handleSaleSubmit);
  el('settingsForm').addEventListener('submit', handleSettingsSubmit);
  el('imageUploadForm').addEventListener('submit', handleImageSubmit);
  el('imageUrlForm').addEventListener('submit', handleImageUrlSubmit);

  el('resetVehicleBtn').addEventListener('click', resetVehicleForm);
  el('resetClientBtn').addEventListener('click', resetClientForm);
  el('resetSaleBtn').addEventListener('click', resetSaleForm);

  el('vehicleSearch').addEventListener('input', renderVehicles);
  el('vehicleStatusFilter').addEventListener('change', renderVehicles);
  el('clientSearch').addEventListener('input', renderClients);

  el('saleBranch').addEventListener('change', syncSharedSelects);

  el('vehicleBrand').addEventListener('change', (evt) => {
    loadVehicleModels(evt.target.value).catch(() => {});
  });

  el('vehicleModel').addEventListener('change', (evt) => {
    const selected = VEHICLE_MODELS.find((m) => m.name === evt.target.value);
    if (!selected) return;
    if (selected.default_vehicle_type) {
      el('vehicleType').value = selected.default_vehicle_type;
    }
    if (selected.default_transmission) {
      el('vehicleTransmission').value = selected.default_transmission;
    }
  });

  el('refreshVehiclesBtn').addEventListener('click', loadVehicles);
  el('refreshClientsBtn').addEventListener('click', loadClients);
  el('refreshSalesBtn').addEventListener('click', loadSales);

  document.body.addEventListener('click', handleMainClick);
  document.body.addEventListener('change', handleMainChange);
  el('imagesList').addEventListener('click', handleImageActions);
  el('closeImagesPanel').addEventListener('click', () => {
    el('imagesPanel').classList.add('hidden');
    ACTIVE_IMAGES_VEHICLE_ID = null;
  });
}

async function bootstrap() {
  if (!ensureAuthenticated()) return;
  try {
    await loadCurrentUser();
    await loadCatalogs();
    await loadUsers();
    await loadBranches();
    await loadVehicles();
    await loadClients();
    await loadSales();
    await loadSettings();
    syncSharedSelects();
    resetVehicleForm();
    resetClientForm();
    resetSaleForm();
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      window.REDLINE.clearToken();
      window.location.href = '../login/index.html';
      return;
    }
    alert(`No se pudo cargar el panel: ${error.message}`);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  wireUi();
  bootstrap();
});
