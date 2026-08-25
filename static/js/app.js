// Small UX helpers for SkillSwap.

document.addEventListener("DOMContentLoaded", function () {
  // Confirm before cancelling a session.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm(form.getAttribute("data-confirm"))) {
        e.preventDefault();
      }
    });
  });

  // Star rating widget: clicking a star sets the hidden input value.
  document.querySelectorAll(".star-input").forEach(function (wrapper) {
    const input = wrapper.querySelector("input[type=hidden]");
    const stars = wrapper.querySelectorAll(".star-pick");
    stars.forEach(function (star) {
      star.addEventListener("click", function () {
        const val = star.getAttribute("data-value");
        input.value = val;
        stars.forEach(function (s) {
          s.classList.toggle("text-warning", parseInt(s.getAttribute("data-value")) <= parseInt(val));
          s.classList.toggle("text-muted", parseInt(s.getAttribute("data-value")) > parseInt(val));
        });
      });
    });
  });

  // Auto-dismiss flash messages after a few seconds.
  document.querySelectorAll(".alert-auto").forEach(function (alertEl) {
    setTimeout(function () {
      alertEl.classList.remove("show");
    }, 4000);
  });

  // Dark mode toggle, persisted in localStorage.
  const themeToggle = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  function syncThemeIcon() {
    const isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
    if (themeIcon) {
      themeIcon.classList.toggle("bi-moon-stars", !isDark);
      themeIcon.classList.toggle("bi-sun-fill", isDark);
    }
  }
  syncThemeIcon();
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const current = document.documentElement.getAttribute("data-bs-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", next);
      localStorage.setItem("skillswap-theme", next);
      syncThemeIcon();
    });
  }
});
