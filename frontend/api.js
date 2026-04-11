(function () {
  const DEFAULT_API_BASE = '/api/v1';
  const KEY_API_BASE = 'REDLINE_API_BASE';
  const KEY_TOKEN = 'REDLINE_TOKEN';

  function getApiBase() {
    return (localStorage.getItem(KEY_API_BASE) || DEFAULT_API_BASE).replace(/\/+$/, '');
  }

  function getApiOrigin() {
    try {
      return new URL(getApiBase()).origin;
    } catch (_) {
      return '';
    }
  }

  function setApiBase(url) {
    if (!url) return;
    localStorage.setItem(KEY_API_BASE, url.replace(/\/+$/, ''));
  }

  function getToken() {
    return localStorage.getItem(KEY_TOKEN) || '';
  }

  function setToken(token) {
    if (!token) return;
    localStorage.setItem(KEY_TOKEN, token);
  }

  function clearToken() {
    localStorage.removeItem(KEY_TOKEN);
  }

  async function request(path, options = {}) {
    const {
      method = 'GET',
      json,
      body,
      token = getToken(),
      headers = {},
      responseType = 'json',
    } = options;

    const reqHeaders = {
      'Accept': responseType === 'blob' ? '*/*' : 'application/json',
      ...headers,
    };

    let finalBody = body;
    if (json !== undefined) {
      reqHeaders['Content-Type'] = 'application/json';
      finalBody = JSON.stringify(json);
    }

    if (finalBody instanceof FormData) {
      delete reqHeaders['Content-Type'];
    }

    if (token) {
      reqHeaders['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${getApiBase()}${path}`, {
      method,
      headers: reqHeaders,
      body: finalBody,
    });

    if (responseType === 'blob') {
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(text || `Error ${res.status}`);
      }
      return res.blob();
    }

    const contentType = res.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');
    const payload = isJson ? await res.json().catch(() => null) : await res.text().catch(() => '');

    if (!res.ok) {
      const message = (payload && payload.detail) ? payload.detail : `Error ${res.status}`;
      const err = new Error(message);
      err.status = res.status;
      err.payload = payload;
      throw err;
    }

    return payload;
  }

  function formatCurrencyRD(value) {
    const n = Number(value);
    if (Number.isNaN(n)) return 'RD$ —';
    return `RD$ ${n.toLocaleString('es-DO', { maximumFractionDigits: 0 })}`;
  }

  function pickCoverImage(vehicle) {
    if (!vehicle || !Array.isArray(vehicle.images) || vehicle.images.length === 0) return '';
    const cover = vehicle.images.find(img => img.is_cover);
    const path = (cover || vehicle.images[0]).file_path;
    if (!path) return '';
    if (typeof path === 'string' && path.startsWith('/')) {
      const origin = getApiOrigin();
      return origin ? `${origin}${path}` : path;
    }
    return path;
  }

  window.REDLINE = {
    getApiBase,
    getApiOrigin,
    setApiBase,
    getToken,
    setToken,
    clearToken,
    request,
    formatCurrencyRD,
    pickCoverImage,
  };
})();
