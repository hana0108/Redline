function el(id) {
  return document.getElementById(id);
}

async function onLogin(evt) {
  evt.preventDefault();

  const email = el("email").value.trim();
  const password = el("password").value;

  const statusEl = el("loginStatus");
  statusEl.textContent = "Iniciando sesión...";
  statusEl.style.color = "";

  try {
    const res = await window.REDLINE.request("/auth/login", {
      method: "POST",
      json: { email, password },
    });

    if (!res || !res.access_token) {
      throw new Error("Respuesta inválida del servidor");
    }

    window.REDLINE.setToken(res.access_token);
    statusEl.textContent = "Acceso concedido. Redirigiendo...";
    statusEl.style.color = "#16a34a";

    setTimeout(() => {
      window.location.href = "../admin/index.html";
    }, 400);
  } catch (e) {
    statusEl.textContent = e.message || "Error inesperado";
    statusEl.style.color = "#dc2626";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  el("loginForm").addEventListener("submit", onLogin);
});