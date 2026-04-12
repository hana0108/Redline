function el(id) { 
  return document.getElementById(id);
}

async function onLogin(evt) {
  evt.preventDefault();

  const email = el("email").value.trim();
  const password = el("password").value;
  const status = el("loginStatus");
  const btn = evt.target.querySelector("button");

  btn.disabled = true;
  btn.textContent = "Entrando...";
  status.style.color = "#333";
  status.textContent = "Validando credenciales...";

  try {
    const res = await window.REDLINE.request("/auth/login", {
      method: "POST",
      json: { email, password },
    });

    if (!res || !res.access_token) {
      throw new Error("Respuesta inválida del servidor");
    }

    window.REDLINE.setToken(res.access_token, res.token_type || "Bearer");

    status.style.color = "green";
    status.textContent = "✅ Acceso concedido. Redirigiendo...";

    btn.textContent = "✔";

    setTimeout(() => {
      window.location.href = "../admin/index.html";
    }, 600);

  } catch (e) {
    status.style.color = "#da2520";
    status.textContent = `❌ ${e.message || "Error inesperado"}`;

    btn.disabled = false;
    btn.textContent = "INICIAR SESIÓN";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  el("apiBaseLabel").textContent = window.REDLINE.getApiBase();
  el("loginForm").addEventListener("submit", onLogin);

  
  const btnInventario = document.getElementById("btnInventario");

  if (btnInventario) {
    btnInventario.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = "login/index.html";
    });
  }
});