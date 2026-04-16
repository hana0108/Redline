function el(id) { return document.getElementById(id); }

let CURRENT_USER = null;
let BRANCHES = [];
let USERS = [];
let ROLES = [];
let VEHICLES = [];
let CLIENTS = [];
let SALES = [];
let CATALOGS = { brands: [], vehicle_types: [], fuel_types: [], transmissions: [], colors: [] };
let VEHICLE_MODELS = [];
let ACTIVE_IMAGES_VEHICLE_ID = null;
let _confirmResolve = null;
let _reserveStatusResolve = null;  // for reserve-client modal

// ── Page navigation ──────────────────────────────────────────────────────────

const PAGE_MAP = {
  dashboard: 'pageDashboard',
  branches:  'pageBranches',
  inventory: 'pageInventory',
  clients:   'pageClients',
  sales:     'pageSales',
  users:     'pageUsers',
  roles:     'pageRoles',
  settings:  'pageSettings',
};

let CURRENT_PAGE = 'dashboard';

function navigateTo(page) {
  if (!PAGE_MAP[page]) return;
  CURRENT_PAGE = page;

  // Toggle page visibility
  Object.values(PAGE_MAP).forEach(id => {
    const node = el(id);
    if (node) node.classList.add('hidden');
  });
  const active = el(PAGE_MAP[page]);
  if (active) active.classList.remove('hidden');

  // Update nav active state
  document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === page);
  });
}

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

const PLACEHOLDER_IMG = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='450'%3E%3Crect fill='%23eef2f6' width='800' height='450'/%3E%3Ctext fill='%2399a3ae' font-family='sans-serif' font-size='32' text-anchor='middle' x='400' y='225'%3ESin imagen%3C/text%3E%3C/svg%3E`;

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
  if (!message) {
    node.style.color = '';
  } else if (isError) {
    node.style.color = '#b11b17';
    toast(message, 'error');
  } else if (!message.endsWith('...')) {
    node.style.color = '#0d7e46';
    toast(message, 'success');
  } else {
    node.style.color = '#67717c';
  }
}

function toast(message, type = 'info') {
  let container = el('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    document.body.appendChild(container);
  }
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
  return new Promise((resolve) => {
    _confirmResolve = resolve;
    el('confirmModalText').textContent = message;
    el('confirmModal').classList.remove('hidden');
  });
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

  // Branch filters for inventory and history
  const allOpt = '<option value="">Todas las sucursales</option>';
  const branchOptions = BRANCHES.map(b => `<option value="${b.id}">${escapeHtml(b.name)}</option>`).join('');
  const branchFilterNode = el('vehicleBranchFilter');
  if (branchFilterNode) {
    const prev = branchFilterNode.value;
    branchFilterNode.innerHTML = allOpt + branchOptions;
    branchFilterNode.value = prev;
  }
  const histBranchNode = el('salesHistoryBranchFilter');
  if (histBranchNode) {
    const prev = histBranchNode.value;
    histBranchNode.innerHTML = allOpt + branchOptions;
    histBranchNode.value = prev;
  }

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
}

async function loadUsers() {
  try {
    USERS = await window.REDLINE.request('/users');
  } catch (error) {
    if (error.status === 403) {
      USERS = CURRENT_USER ? [{ id: CURRENT_USER.id, full_name: CURRENT_USER.full_name, role: CURRENT_USER.role, email: CURRENT_USER.email }] : [];
    } else {
      throw error;
    }
  }
  setText('metricPermissions', String(USERS.length));
  renderUsers();
  populateSelect('userRole', ROLES, 'Selecciona un rol', el('userRole')?.value,
    (r) => ({ value: r.id, label: r.name }));
}

function renderUsers() {
  const container = el('userList');
  if (!container) return;
  if (!USERS.length) {
    container.innerHTML = '<p class="muted" style="padding:12px">No hay usuarios registrados.</p>';
    return;
  }
  container.innerHTML = USERS.map(user => {
    const isActive = user.status === 'active';
    const roleName = user.role?.name || (typeof user.role === 'string' ? user.role : '?');
    const branchNames = (user.branch_ids || [])
      .map(bid => BRANCHES.find(b => b.id === bid)?.name || bid)
      .join(', ') || 'Sin sucursal';
    return `
      <div class="user-card">
        <div class="user-card-header">
          <div>
            <h4>${escapeHtml(user.full_name)}</h4>
            <span class="badge ${isActive ? 'available' : 'other'}">${isActive ? 'Activo' : 'Inactivo'}</span>
            <span class="badge info">${escapeHtml(roleName)}</span>
          </div>
          <div class="entity-actions">
            <button class="btn secondary small" data-action="edit-user" data-id="${user.id}">Editar</button>
            <button class="btn warning small" data-action="toggle-user" data-id="${user.id}" data-status="${user.status}">
              ${isActive ? 'Desactivar' : 'Activar'}
            </button>
            <button class="btn danger small" data-action="delete-user" data-id="${user.id}">Eliminar</button>
          </div>
        </div>
        <div class="user-meta">
          <span>✉ ${escapeHtml(user.email)}</span>
          ${user.phone ? `<span>📞 ${escapeHtml(user.phone)}</span>` : ''}
          <span>🏢 ${escapeHtml(branchNames)}</span>
        </div>
      </div>`;
  }).join('');
}

function fillUserForm(user) {
  el('userId').value = user.id;
  el('userFullName').value = user.full_name || '';
  el('userEmail').value = user.email || '';
  el('userPhone').value = user.phone || '';
  el('userPassword').value = '';
  el('userPassword').required = false;
  el('userPassword').placeholder = 'Contraseña (dejar vacío para no cambiar)';
  el('userRole').value = user.role?.id || '';
  setText('userFormTitle', 'Editar usuario');
  setText('userSubmitBtn', 'Guardar cambios');
  renderBranchesChecklist(user.branch_ids || []);
  navigateTo('users');
}

function resetUserForm() {
  el('userId').value = '';
  el('userFullName').value = '';
  el('userEmail').value = '';
  el('userPhone').value = '';
  el('userPassword').value = '';
  el('userPassword').required = true;
  el('userPassword').placeholder = 'Contraseña (mín. 8 caracteres)';
  el('userRole').value = '';
  setText('userFormTitle', 'Nuevo usuario');
  setText('userSubmitBtn', 'Crear usuario');
  showMessage('userFormStatus', '');
  renderBranchesChecklist([]);
}

function renderBranchesChecklist(selectedIds = []) {
  const container = el('userBranchesChecklist');
  if (!container) return;
  if (!BRANCHES.length) {
    container.innerHTML = '<p class="muted" style="font-size:13px">No hay sucursales creadas.</p>';
    return;
  }
  container.innerHTML = BRANCHES.map(b => `
    <label class="branch-check-item">
      <input type="checkbox" name="userBranch" value="${b.id}"
        ${selectedIds.map(String).includes(String(b.id)) ? 'checked' : ''} />
      ${escapeHtml(b.name)}
    </label>`).join('');
}

async function handleUserSubmit(evt) {
  evt.preventDefault();
  const id = el('userId').value;
  const password = el('userPassword').value;
  const checkedBranches = [...document.querySelectorAll('input[name="userBranch"]:checked')]
    .map(cb => cb.value);

  const payload = {
    full_name: el('userFullName').value.trim(),
    email: el('userEmail').value.trim(),
    phone: el('userPhone').value.trim() || null,
    role_id: el('userRole').value,
    branch_ids: checkedBranches,
  };
  if (!id) {
    payload.password = password;
  } else if (password) {
    payload.password = password;
  }

  showMessage('userFormStatus', 'Guardando...');
  try {
    if (id) {
      await window.REDLINE.request(`/users/${id}`, { method: 'PATCH', json: payload });
      if (checkedBranches !== undefined) {
        await window.REDLINE.request(`/users/${id}/branches`, {
          method: 'PUT', json: { branch_ids: checkedBranches },
        });
      }
    } else {
      await window.REDLINE.request('/users', { method: 'POST', json: payload });
    }
    showMessage('userFormStatus', id ? 'Usuario actualizado.' : 'Usuario creado.');
    resetUserForm();
    await loadUsers();
  } catch (err) {
    showMessage('userFormStatus', err.message, true);
  }
}

// ── Roles ────────────────────────────────────────────────────────────────────

async function loadRoles() {
  try {
    ROLES = await window.REDLINE.request('/roles');
    renderRoles();
    populateSelect('userRole', ROLES, 'Selecciona un rol', el('userRole')?.value,
      (r) => ({ value: r.id, label: r.name }));
  } catch (_) {
    ROLES = [];
  }
}

function renderRoles() {
  const container = el('roleList');
  if (!container) return;
  if (!ROLES.length) {
    container.innerHTML = '<p class="muted" style="padding:12px">No hay roles disponibles.</p>';
    return;
  }
  container.innerHTML = ROLES.map(role => `
    <div class="role-card">
      <h4>${escapeHtml(role.name)}</h4>
      ${role.description ? `<p class="role-desc">${escapeHtml(role.description)}</p>` : ''}
      <div class="permissions-list">
        ${(role.permission_codes || []).length
          ? role.permission_codes.map(p => `<span class="perm-tag">${escapeHtml(p)}</span>`).join('')
          : '<span class="muted" style="font-size:13px">Sin permisos asignados</span>'}
      </div>
    </div>`).join('');
}

async function loadBranches() {
  BRANCHES = await window.REDLINE.request('/branches');
  setText('metricBranches', String(BRANCHES.length));

  el('branchList').innerHTML = BRANCHES.length
    ? BRANCHES.map(branch => {
        const isActive = branch.status === 'active';
        return `
          <div class="entity-card">
            <div class="entity-card-header">
              <div>
                <h4>${escapeHtml(branch.name)}</h4>
                <span class="badge ${isActive ? 'available' : 'other'}">${isActive ? 'Activa' : 'Inactiva'}</span>
              </div>
            </div>
            <div class="muted" style="font-size:13px; margin: 6px 0 10px;">
              ${escapeHtml(branch.address || 'Sin dirección')}
              ${branch.phone ? ` · ${escapeHtml(branch.phone)}` : ''}
              ${branch.email ? ` · ${escapeHtml(branch.email)}` : ''}
            </div>
            <div class="entity-actions">
              <button class="btn secondary small" data-action="edit-branch" data-id="${branch.id}">Editar</button>
              <button class="btn ${isActive ? 'warning' : 'success'} small" data-action="toggle-branch" data-id="${branch.id}">${isActive ? 'Desactivar' : 'Activar'}</button>
              <button class="btn danger small" data-action="delete-branch" data-id="${branch.id}">Eliminar</button>
            </div>
          </div>
        `;
      }).join('')
    : '<div class="muted">No hay sucursales registradas todavía.</div>';

  syncSharedSelects();
}

function vehicleCard(vehicle) {
  const img = window.REDLINE.pickCoverImage(vehicle) || PLACEHOLDER_IMG;
  const branch = BRANCHES.find(b => b.id === vehicle.branch_id);
  const branchInactive = branch && branch.status !== 'active';
  const inactiveBadge = branchInactive
    ? `<span class="badge other branch-inactive-badge" title="Sucursal desactivada">⚠ Sucursal inactiva</span>`
    : '';
  return `
    <article class="vehicle-card${branchInactive ? ' vehicle-card--branch-inactive' : ''}">
      <div class="vehicle-img-wrap">
        <img src="${escapeHtml(img)}" alt="${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)}" loading="lazy" />
        <span class="vehicle-status-overlay badge ${badgeClass(vehicle.status)}">${escapeHtml(STATUS_LABELS[vehicle.status] || vehicle.status)}</span>
      </div>
      <div>
        <div class="entity-card-header">
          <div>
            <h4>${escapeHtml(vehicle.brand)} ${escapeHtml(vehicle.model)} <small class="muted" style="font-size:14px;font-weight:500">${vehicle.vehicle_year}</small></h4>
            <div class="muted" style="font-size:13px">VIN: ${escapeHtml(vehicle.vin)} &middot; Placa: ${escapeHtml(vehicle.plate || 'N/D')} &middot; ${escapeHtml(getBranchName(vehicle.branch_id))}</div>
          </div>
          ${inactiveBadge}
        </div>
        <div class="vehicle-price">${window.REDLINE.formatCurrencyRD(vehicle.price)}</div>
        <div class="meta-grid">
          <div class="meta-pill">${(vehicle.mileage || 0).toLocaleString('es-DO')} km</div>
          <div class="meta-pill">${escapeHtml(vehicle.transmission || 'N/D')}</div>
          <div class="meta-pill">${escapeHtml(vehicle.fuel_type || 'N/D')}</div>
          <div class="meta-pill">${escapeHtml(vehicle.color || 'N/D')}</div>
        </div>
        <div class="vehicle-actions">
          <button class="btn secondary small" data-action="edit-vehicle" data-id="${vehicle.id}">Editar</button>
          <button class="btn secondary small" data-action="images" data-id="${vehicle.id}">Imágenes</button>
          <button class="btn secondary small" data-action="vehicle-history" data-id="${vehicle.id}">Historial</button>
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
  const branchId = el('vehicleBranchFilter')?.value || '';
  const filtered = VEHICLES.filter(vehicle => {
    if (vehicle.status === 'reservado') return false;  // reservados tienen su propia sección
    const text = `${vehicle.brand} ${vehicle.model} ${vehicle.vin} ${vehicle.plate || ''}`.toLowerCase();
    return (!search || text.includes(search))
      && (!status || vehicle.status === status)
      && (!branchId || String(vehicle.branch_id) === branchId);
  });

  setText('metricVehicles', String(VEHICLES.length));
  el('vehicleList').innerHTML = filtered.length
    ? filtered.map(vehicleCard).join('')
    : '<div class="muted">No hay vehículos que coincidan con el filtro.</div>';
}

function renderReserved() {
  const reserved = VEHICLES.filter(v => v.status === 'reservado');
  el('reservedList').innerHTML = reserved.length
    ? reserved.map(v => {
        const clientName = v.reserved_client_id ? getClientName(v.reserved_client_id) : 'Sin cliente asociado';
        return vehicleCard(v).replace(
          '<div class="vehicle-actions">',
          `<div class="reserved-client-info"><span class="meta-pill">Cliente: ${escapeHtml(clientName)}</span></div><div class="vehicle-actions">`
        );
      }).join('')
    : '<div class="muted" style="padding: 28px 0; text-align: center;">No hay vehículos reservados actualmente.</div>';
}

function renderSalesHistory() {
  const branchId = el('salesHistoryBranchFilter')?.value || '';
  const search = el('salesHistorySearch')?.value.trim().toLowerCase() || '';
  const statusFilter = el('salesHistoryStatusFilter')?.value || '';
  const filtered = SALES.filter(item => {
    const clientName = getClientName(item.client_id).toLowerCase();
    const vehicleLabel = getVehicleLabel(item.vehicle_id).toLowerCase();
    return (!branchId || String(item.branch_id) === branchId)
      && (!statusFilter || item.status === statusFilter)
      && (!search || clientName.includes(search) || vehicleLabel.includes(search));
  });
  const sorted = [...filtered].sort((a, b) => new Date(b.sale_date) - new Date(a.sale_date));
  el('salesHistoryList').innerHTML = sorted.length
    ? sorted.map(item => `
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
            <span class="meta-pill">Precio: ${window.REDLINE.formatCurrencyRD(item.sale_price)}</span>
            ${item.profit != null ? `<span class="meta-pill">Ganancia: ${window.REDLINE.formatCurrencyRD(item.profit)}</span>` : ''}
            <span class="meta-pill">Pago: ${escapeHtml(item.payment_method || 'No indicado')}</span>
            <span class="meta-pill">Vendedor: ${escapeHtml(item.seller_user_id ? getUserName(item.seller_user_id) : 'Sin vendedor')}</span>
          </div>
          <div class="muted">Fecha: ${formatDateTime(item.sale_date)}</div>
          <div class="entity-actions" style="margin-top: 10px;">
            <button class="btn secondary small" data-action="edit-sale" data-id="${item.id}">Editar</button>
            <button class="btn secondary small" data-action="pdf-sale" data-id="${item.id}">PDF</button>
          </div>
        </div>
      `).join('')
    : '<div class="muted" style="padding: 12px 0;">No hay ventas para los filtros aplicados.</div>';
}

async function loadVehicles() {
  VEHICLES = await window.REDLINE.request('/vehicles');
  renderVehicles();
  renderReserved();
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
  navigateTo('inventory');
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
  navigateTo('clients');
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
  const client = CLIENTS.find(item => item.id === clientId);
  el('clientHistoryTitle').textContent = `Historial de ${client?.full_name || 'cliente'}`;
  el('clientHistorySubtitle').textContent = `${history.sales.length} venta(s) · ${(history.status_events || []).length} cambio(s) de estado`;

  const salesHtml = history.sales.length
    ? `<ul>${history.sales.map(item => `
        <li>
          <strong>${escapeHtml(getVehicleLabel(item.vehicle_id))}</strong>
          <div class="muted">${window.REDLINE.formatCurrencyRD(item.sale_price)} · ${formatDateTime(item.sale_date)} · <span class="badge ${badgeClass(item.status)} badge-inline">${escapeHtml(SALE_LABELS[item.status] || item.status)}</span></div>
        </li>`).join('')}</ul>`
    : '<div class="muted">Sin ventas.</div>';

  const eventsHtml = history.status_events && history.status_events.length
    ? `<ul>${history.status_events.map(ev => `
        <li>
          <strong>${escapeHtml(getVehicleLabel(ev.vehicle_id))}</strong>
          <div class="muted">
            ${ev.old_status ? `<span class="badge ${badgeClass(ev.old_status)} badge-inline">${escapeHtml(STATUS_LABELS[ev.old_status] || ev.old_status)}</span> → ` : ''}
            <span class="badge ${badgeClass(ev.new_status)} badge-inline">${escapeHtml(STATUS_LABELS[ev.new_status] || ev.new_status)}</span>
            · ${formatDateTime(ev.created_at)}
            ${ev.notes ? ` · ${escapeHtml(ev.notes)}` : ''}
          </div>
        </li>`).join('')}</ul>`
    : '<div class="muted">Sin cambios de estado.</div>';

  el('clientHistoryContent').innerHTML = `
    <div class="history-grid" style="margin-top:4px">
      <div class="history-box">
        <h5>Ventas (${history.sales.length})</h5>
        ${salesHtml}
      </div>
      <div class="history-box">
        <h5>Cambios de estado (${(history.status_events || []).length})</h5>
        ${eventsHtml}
      </div>
    </div>
  `;

  el('clientHistoryModal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

async function showVehicleHistory(vehicleId) {
  const vehicle = VEHICLES.find(v => v.id === vehicleId);
  const modal = el('vehicleHistoryModal');
  el('vehicleHistorySubtitle').textContent = vehicle ? `${vehicle.brand} ${vehicle.model} · ${vehicle.vin}` : vehicleId;
  el('vehicleHistoryList').innerHTML = '<div class="muted">Cargando...</div>';
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  try {
    const events = await window.REDLINE.request(`/vehicles/${vehicleId}/status-history`);
    if (!events.length) {
      el('vehicleHistoryList').innerHTML = '<div class="muted" style="padding:20px 0">Sin cambios de estado registrados.</div>';
      return;
    }
    el('vehicleHistoryList').innerHTML = events.map(ev => `
      <div class="history-event-row">
        <div class="history-event-badges">
          ${ev.old_status ? `<span class="badge ${badgeClass(ev.old_status)}">${escapeHtml(STATUS_LABELS[ev.old_status] || ev.old_status)}</span><span class="history-arrow">→</span>` : ''}
          <span class="badge ${badgeClass(ev.new_status)}">${escapeHtml(STATUS_LABELS[ev.new_status] || ev.new_status)}</span>
        </div>
        <div class="history-event-meta">
          <span>${formatDateTime(ev.created_at)}</span>
          ${ev.changed_by ? `<span>· Por: ${escapeHtml(getUserName(ev.changed_by))}</span>` : ''}
          ${ev.client_id ? `<span>· Cliente: ${escapeHtml(getClientName(ev.client_id))}</span>` : ''}
          ${ev.notes ? `<span class="muted">· ${escapeHtml(ev.notes)}</span>` : ''}
        </div>
      </div>
    `).join('');
  } catch (err) {
    el('vehicleHistoryList').innerHTML = `<div class="muted" style="color:#b11b17">Error al cargar historial.</div>`;
  }
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
  renderSalesHistory();
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
  navigateTo('sales');
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
      <div class="muted">Orden: ${image.sort_order}${image.is_cover ? ' &middot; <strong>Portada</strong>' : ''}</div>
      <div class="entity-actions">
        ${image.is_cover ? '' : `<button class="btn secondary small" data-image-action="cover" data-image-id="${image.id}">Portada</button>`}
        <button class="btn danger small" data-image-action="delete" data-image-id="${image.id}">Eliminar</button>
      </div>
    </div>
  `).join('') : '<div class="muted" style="padding: 16px 0;">Sin imágenes cargadas aún.</div>';
}

async function openImagesPanel(vehicle) {
  ACTIVE_IMAGES_VEHICLE_ID = vehicle.id;
  el('imagesModal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  setText('imagesTitle', `${vehicle.brand} ${vehicle.model} · ${vehicle.vin}`);
  await refreshImages();
}

async function handleBranchSubmit(evt) {
  evt.preventDefault();
  const branchId = el('branchId').value;
  const btn = el('branchSubmitBtn');
  btn.disabled = true;
  const payload = {
    name: el('branchName').value.trim(),
    phone: el('branchPhone').value.trim() || null,
    email: el('branchEmail').value.trim() || null,
    address: el('branchAddress').value.trim() || null,
  };
  showMessage('branchFormStatus', branchId ? 'Actualizando sucursal...' : 'Guardando sucursal...');
  try {
    if (branchId) {
      await window.REDLINE.request(`/branches/${branchId}`, { method: 'PATCH', json: payload });
      showMessage('branchFormStatus', 'Sucursal actualizada correctamente.');
    } else {
      await window.REDLINE.request('/branches', { method: 'POST', json: payload });
      showMessage('branchFormStatus', 'Sucursal creada correctamente.');
    }
    resetBranchForm();
    await loadBranches();
  } catch (error) {
    showMessage('branchFormStatus', error.message, true);
  } finally {
    btn.disabled = false;
  }
}

function fillBranchForm(branch) {
  el('branchId').value = branch.id;
  el('branchName').value = branch.name;
  el('branchPhone').value = branch.phone || '';
  el('branchEmail').value = branch.email || '';
  el('branchAddress').value = branch.address || '';
  setText('branchFormTitle', 'Editar sucursal');
  el('branchSubmitBtn').textContent = 'Guardar cambios';
  el('branchFormStatus').textContent = '';
  navigateTo('branches');
}

function resetBranchForm() {
  el('branchId').value = '';
  el('branchForm').reset();
  setText('branchFormTitle', 'Nueva sucursal');
  el('branchSubmitBtn').textContent = 'Crear sucursal';
  el('branchFormStatus').textContent = '';
}

async function handleVehicleSubmit(evt) {
  evt.preventDefault();
  const vehicleId = el('vehicleId').value;
  const btn = el('vehicleForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
  }
}

async function handleClientSubmit(evt) {
  evt.preventDefault();
  const clientId = el('clientId').value;
  const btn = el('clientForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
  }
}

async function handleSaleSubmit(evt) {
  evt.preventDefault();
  const saleId = el('saleId').value;
  const btn = el('saleForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
  }
}

async function handleSettingsSubmit(evt) {
  evt.preventDefault();
  const btn = el('settingsForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
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
  const btn = el('imageUploadForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
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

  const btn = el('imageUrlForm').querySelector('[type="submit"]');
  btn.disabled = true;
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
  } finally {
    btn.disabled = false;
  }
}

async function handleMainClick(evt) {
  const button = evt.target.closest('[data-action]');
  if (!button) return;
  const action = button.dataset.action;
  const id = button.dataset.id;
  try {
    if (action === 'edit-branch') {
      const branch = BRANCHES.find(item => item.id === id);
      if (branch) fillBranchForm(branch);
      return;
    }
    if (action === 'toggle-branch') {
      const branch = BRANCHES.find(item => item.id === id);
      if (!branch) return;
      const newStatus = branch.status === 'active' ? 'inactive' : 'active';
      await window.REDLINE.request(`/branches/${id}`, { method: 'PATCH', json: { status: newStatus } });
      await loadBranches();
      return;
    }
    if (action === 'delete-branch') {
      if (!await askConfirmation('¿Eliminar esta sucursal? Solo es posible si no tiene vehículos ni ventas asociadas.')) return;
      await window.REDLINE.request(`/branches/${id}`, { method: 'DELETE' });
      await loadBranches();
      return;
    }
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
    if (action === 'vehicle-history') {
      await showVehicleHistory(id);
      return;
    }
    if (action === 'delete-vehicle') {
      if (!await askConfirmation('¿Eliminar este vehículo?')) return;
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
      if (!await askConfirmation('¿Eliminar este cliente?')) return;
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
      if (!await askConfirmation('¿Eliminar esta venta? El vehículo volverá a estar disponible.')) return;
      await window.REDLINE.request(`/sales/${id}`, { method: 'DELETE' });
      await Promise.all([loadVehicles(), loadSales()]);
      return;
    }
    if (action === 'edit-user') {
      const user = USERS.find(item => item.id === id);
      if (user) fillUserForm(user);
      return;
    }
    if (action === 'toggle-user') {
      const user = USERS.find(item => item.id === id);
      if (!user) return;
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      await window.REDLINE.request(`/users/${id}/status`, { method: 'PATCH', json: { status: newStatus } });
      await loadUsers();
      return;
    }
    if (action === 'delete-user') {
      if (!await askConfirmation('¿Eliminar este usuario? Esta acción no se puede deshacer.')) return;
      await window.REDLINE.request(`/users/${id}`, { method: 'DELETE' });
      await loadUsers();
      return;
    }
  } catch (error) {
    toast(error.message, 'error');
  }
}

function askReserveClient(vehicleId, currentSelectEl) {
  return new Promise((resolve) => {
    _reserveStatusResolve = resolve;
    const modal = el('reserveClientModal');
    el('reserveClientVehicleId').value = vehicleId;
    el('reserveClientOriginalStatus').value = currentSelectEl.dataset.prevStatus || '';
    el('reserveClientSearch').value = '';
    el('reserveClientId').value = '';
    el('reserveClientName').value = '';
    el('reserveClientPhone').value = '';
    el('reserveClientEmail').value = '';
    renderReserveClientList('');
    modal.classList.remove('hidden');
  });
}

function renderReserveClientList(search) {
  const lower = search.toLowerCase();
  const filtered = CLIENTS.filter(c => {
    const text = `${c.full_name} ${c.phone || ''} ${c.email || ''} ${c.document_number || ''}`.toLowerCase();
    return !lower || text.includes(lower);
  });
  const list = el('reserveClientList');
  list.innerHTML = filtered.slice(0, 8).map(c => `
    <div class="reserve-client-item" data-client-id="${c.id}" data-client-name="${escapeHtml(c.full_name)}">
      <strong>${escapeHtml(c.full_name)}</strong>
      <span class="muted">${escapeHtml(c.phone || c.email || '')}</span>
    </div>
  `).join('') || '<div class="muted">No se encontraron clientes.</div>';
  list.querySelectorAll('.reserve-client-item').forEach(item => {
    item.addEventListener('click', () => {
      el('reserveClientId').value = item.dataset.clientId;
      list.querySelectorAll('.reserve-client-item').forEach(i => i.classList.remove('selected'));
      item.classList.add('selected');
      el('reserveClientName').value = '';
      el('reserveClientPhone').value = '';
      el('reserveClientEmail').value = '';
    });
  });
}

async function confirmReserveClient() {
  const vehicleId = el('reserveClientVehicleId').value;
  const existingClientId = el('reserveClientId').value;
  const newName = el('reserveClientName').value.trim();
  const newPhone = el('reserveClientPhone').value.trim();
  const newEmail = el('reserveClientEmail').value.trim();

  if (!existingClientId && !newName) {
    toast('Selecciona un cliente existente o ingresa el nombre del nuevo cliente.', 'error');
    return;
  }

  let clientId = existingClientId;
  try {
    if (!existingClientId && newName) {
      const newClient = await window.REDLINE.request('/clients', {
        method: 'POST',
        json: {
          full_name: newName,
          phone: newPhone || null,
          email: newEmail || null,
        },
      });
      clientId = newClient.id;
      await loadClients();
    }
    el('reserveClientModal').classList.add('hidden');
    if (_reserveStatusResolve) {
      _reserveStatusResolve({ confirmed: true, clientId });
      _reserveStatusResolve = null;
    }
  } catch (err) {
    toast(err.message, 'error');
  }
}

function cancelReserveClient() {
  el('reserveClientModal').classList.add('hidden');
  if (_reserveStatusResolve) {
    _reserveStatusResolve({ confirmed: false });
    _reserveStatusResolve = null;
  }
}

async function handleMainChange(evt) {
  const target = evt.target;
  const action = target?.dataset?.action;
  if (!action) return;
  try {
    if (action === 'status') {
      const newStatus = target.value;
      if (newStatus === 'reservado') {
        target.dataset.prevStatus = target.dataset.prevStatus || VEHICLES.find(v => v.id === target.dataset.id)?.status || '';
        const result = await askReserveClient(target.dataset.id, target);
        if (!result.confirmed) {
          target.value = target.dataset.prevStatus || 'disponible';
          return;
        }
        await window.REDLINE.request(`/vehicles/${target.dataset.id}/status`, {
          method: 'PATCH',
          json: { status: newStatus, client_id: result.clientId, notes: null },
        });
      } else {
        await window.REDLINE.request(`/vehicles/${target.dataset.id}/status`, { method: 'PATCH', json: { status: newStatus, notes: null } });
      }
      await loadVehicles();
      return;
    }
  } catch (error) {
    toast(error.message, 'error');
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
      if (!await askConfirmation('¿Eliminar esta imagen?')) return;
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

  // ── Sidebar navigation ──────────────────────────────────────────────────────
  document.getElementById('sidebarNav').addEventListener('click', (evt) => {
    const btn = evt.target.closest('[data-page]');
    if (btn) navigateTo(btn.dataset.page);
  });

  // Dashboard shortcut buttons
  document.addEventListener('click', (evt) => {
    const btn = evt.target.closest('[data-goto]');
    if (btn) navigateTo(btn.dataset.goto);
  });

  // ── Forms ───────────────────────────────────────────────────────────────────
  el('branchForm').addEventListener('submit', handleBranchSubmit);
  el('vehicleForm').addEventListener('submit', handleVehicleSubmit);
  el('clientForm').addEventListener('submit', handleClientSubmit);
  el('saleForm').addEventListener('submit', handleSaleSubmit);
  el('settingsForm').addEventListener('submit', handleSettingsSubmit);
  el('imageUploadForm').addEventListener('submit', handleImageSubmit);
  el('imageUrlForm').addEventListener('submit', handleImageUrlSubmit);
  el('userForm').addEventListener('submit', handleUserSubmit);

  // ── Reset buttons ────────────────────────────────────────────────────────────
  el('resetVehicleBtn').addEventListener('click', resetVehicleForm);
  el('resetClientBtn').addEventListener('click', resetClientForm);
  el('resetSaleBtn').addEventListener('click', resetSaleForm);
  el('resetBranchBtn').addEventListener('click', resetBranchForm);
  el('resetUserBtn').addEventListener('click', resetUserForm);

  // ── Refresh buttons ──────────────────────────────────────────────────────────
  el('refreshVehiclesBtn').addEventListener('click', loadVehicles);
  el('refreshClientsBtn').addEventListener('click', loadClients);
  el('refreshSalesBtn').addEventListener('click', loadSales);
  el('refreshReservedBtn').addEventListener('click', loadVehicles);
  el('refreshSalesHistoryBtn').addEventListener('click', loadSales);
  el('refreshUsersBtn').addEventListener('click', loadUsers);
  el('refreshRolesBtn').addEventListener('click', loadRoles);

  // ── Filters & search ─────────────────────────────────────────────────────────
  el('vehicleSearch').addEventListener('input', renderVehicles);
  el('vehicleStatusFilter').addEventListener('change', renderVehicles);
  el('vehicleBranchFilter').addEventListener('change', renderVehicles);
  el('clientSearch').addEventListener('input', renderClients);
  el('salesHistoryBranchFilter').addEventListener('change', renderSalesHistory);
  el('salesHistoryStatusFilter').addEventListener('change', renderSalesHistory);
  el('salesHistorySearch').addEventListener('input', renderSalesHistory);

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

  // ── Delegated click/change ────────────────────────────────────────────────────
  document.body.addEventListener('click', handleMainClick);
  document.body.addEventListener('change', handleMainChange);
  el('imagesList').addEventListener('click', handleImageActions);

  // ── Modals ───────────────────────────────────────────────────────────────────
  function closeImagesModal() {
    el('imagesModal').classList.add('hidden');
    document.body.style.overflow = '';
    ACTIVE_IMAGES_VEHICLE_ID = null;
  }
  el('closeImagesPanel').addEventListener('click', closeImagesModal);
  el('imagesModal').addEventListener('click', (evt) => {
    if (evt.target === el('imagesModal')) closeImagesModal();
  });

  function closeVehicleHistoryModal() {
    el('vehicleHistoryModal').classList.add('hidden');
    document.body.style.overflow = '';
  }
  el('closeVehicleHistoryBtn').addEventListener('click', closeVehicleHistoryModal);
  el('vehicleHistoryModal').addEventListener('click', (evt) => {
    if (evt.target === el('vehicleHistoryModal')) closeVehicleHistoryModal();
  });

  function closeClientHistoryModal() {
    el('clientHistoryModal').classList.add('hidden');
    document.body.style.overflow = '';
  }
  el('closeClientHistoryBtn').addEventListener('click', closeClientHistoryModal);
  el('clientHistoryModal').addEventListener('click', (evt) => {
    if (evt.target === el('clientHistoryModal')) closeClientHistoryModal();
  });
  el('confirmOkBtn').addEventListener('click', () => {
    el('confirmModal').classList.add('hidden');
    if (_confirmResolve) { _confirmResolve(true); _confirmResolve = null; }
  });
  el('confirmCancelBtn').addEventListener('click', () => {
    el('confirmModal').classList.add('hidden');
    if (_confirmResolve) { _confirmResolve(false); _confirmResolve = null; }
  });

  el('reserveClientConfirmBtn').addEventListener('click', confirmReserveClient);
  el('reserveClientCancelBtn').addEventListener('click', cancelReserveClient);
  el('reserveClientCancelBtn2').addEventListener('click', () => el('reserveClientCancelBtn').click());
  el('reserveClientSearch').addEventListener('input', (evt) => {
    renderReserveClientList(evt.target.value);
  });

  document.addEventListener('keydown', (evt) => {
    if (evt.key === 'Escape') {
      if (!el('imagesModal').classList.contains('hidden')) closeImagesModal();
      if (!el('vehicleHistoryModal').classList.contains('hidden')) closeVehicleHistoryModal();
      if (!el('clientHistoryModal').classList.contains('hidden')) closeClientHistoryModal();
      if (!el('confirmModal').classList.contains('hidden')) {
        el('confirmModal').classList.add('hidden');
        if (_confirmResolve) { _confirmResolve(false); _confirmResolve = null; }
      }
      if (!el('reserveClientModal').classList.contains('hidden')) cancelReserveClient();
    }
  });
}

async function bootstrap() {
  if (!ensureAuthenticated()) return;
  const overlay = el('appLoadingOverlay');
  try {
    await loadCurrentUser();
    await Promise.all([loadCatalogs(), loadRoles()]);
    await Promise.all([loadUsers(), loadBranches()]);
    await Promise.all([loadVehicles(), loadClients()]);
    await loadSales();
    await loadSettings();
    syncSharedSelects();
    resetVehicleForm();
    resetClientForm();
    resetSaleForm();
    resetUserForm();
    navigateTo('dashboard');
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      window.REDLINE.clearToken();
      window.location.href = '../login/index.html';
      return;
    }
    toast(`No se pudo cargar el panel: ${error.message}`, 'error');
  } finally {
    if (overlay) overlay.classList.add('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  wireUi();
  bootstrap();
});
