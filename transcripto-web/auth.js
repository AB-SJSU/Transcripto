(function () {
  "use strict";

  function apiBase() {
    var raw = typeof window.__API_BASE__ === "string" ? window.__API_BASE__.trim() : "";
    return raw.replace(/\/+$/, "");
  }

  function showError(message) {
    var el = document.getElementById("error-banner");
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function hideError() {
    document.getElementById("error-banner").classList.add("hidden");
  }

  function showSuccess(message) {
    var el = document.getElementById("success-banner");
    el.textContent = message;
    el.classList.remove("hidden");
  }

  function hideSuccess() {
    document.getElementById("success-banner").classList.add("hidden");
  }

  function setButtonBusy(btn, busy, idleLabel) {
    btn.disabled = !!busy;
    btn.textContent = busy ? "Working…" : idleLabel;
  }

  async function fetchJson(url, options) {
    var res = await fetch(url, options);
    var text = await res.text();
    var data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      /* ignore */
    }
    if (!res.ok) {
      var detail =
        data && typeof data.detail === "string"
          ? data.detail
          : text || res.statusText || "Request failed";
      throw new Error(detail);
    }
    return data;
  }

  document.getElementById("login-form").addEventListener("submit", function (e) {
    e.preventDefault();
    hideError();
    hideSuccess();

    var base = apiBase();
    if (!base) {
      showError(
        "Set window.__API_BASE__ in auth.html (or inject at deploy time) to your API base URL."
      );
      return;
    }

    var email = document.getElementById("login-email").value.trim();
    var password = document.getElementById("login-password").value;
    var btn = document.getElementById("login-submit");

    if (!email || !password) {
      showError("Enter email and password.");
      return;
    }

    setButtonBusy(btn, true, "Log in");
    fetchJson(base + "/login", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email: email, password: password }),
    })
      .then(function () {
        try {
          sessionStorage.setItem("transcriptoLoggedIn", "1");
        } catch (_) {}
        window.location.href = "index.html";
      })
      .catch(function (err) {
        showError(err.message || String(err));
        setButtonBusy(btn, false, "Log in");
      });
  });

  document.getElementById("signup-form").addEventListener("submit", function (e) {
    e.preventDefault();
    hideError();
    hideSuccess();

    var base = apiBase();
    if (!base) {
      showError(
        "Set window.__API_BASE__ in auth.html (or inject at deploy time) to your API base URL."
      );
      return;
    }

    var email = document.getElementById("signup-email").value.trim();
    var password = document.getElementById("signup-password").value;
    var btn = document.getElementById("signup-submit");

    if (!email || !password) {
      showError("Enter email and password.");
      return;
    }

    setButtonBusy(btn, true, "Create account");
    fetchJson(base + "/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ email: email, password: password }),
    })
      .then(function () {
        showSuccess(
          "Account created. Please log in above using the same email and password you just entered."
        );
        setButtonBusy(btn, false, "Create account");
      })
      .catch(function (err) {
        showError(err.message || String(err));
        setButtonBusy(btn, false, "Create account");
      });
  });
})();
