// MediShop Pro — shared JS
// CSRF and API helpers are defined inline in base.html
// This file holds any additional page-specific utilities

// Auto-dismiss Django messages after 5s
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    document.querySelectorAll('.toast').forEach(t => {
      t.style.opacity = '0';
      t.style.transition = '.4s';
      setTimeout(() => t.remove(), 400);
    });
  }, 5000);
});
