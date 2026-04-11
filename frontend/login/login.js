function el(id) {
  return document.getElementById(id);
}

async function onLogin(evt) {
  evt.preventDefault();

  const email = el("email").value.trim();
  const password = el("password").value;

  el("loginStatus").textContent = "Iniciando sesión...";

  try {
    const res = await window.REDLINE.request("/auth/login", {
      method: "POST",
      json: { email, password },
    });

    if (!res || !res.access_token) {
      throw new Error("Respuesta inválida del servidor");
    }

    window.REDLINE.setToken(res.access_token, res.token_type || "Bearer");
    el("loginStatus").textContent = "✅ Login exitoso. Redirigiendo al backoffice...";

    setTimeout(() => {
      window.location.href = "../admin/index.html";
    }, 400);
  } catch (e) {
    el("loginStatus").textContent = `❌ ${e.message || "Error inesperado"}`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  el("apiBaseLabel").textContent = window.REDLINE.getApiBase();
  el("loginForm").addEventListener("submit", onLogin);
});