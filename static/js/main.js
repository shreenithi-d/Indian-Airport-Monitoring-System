// Main application JavaScript
document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 5 seconds
  setTimeout(function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // Password visibility toggle
  const togglePassBtns = document.querySelectorAll('.toggle-password-btn');
  togglePassBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetInput = document.querySelector(btn.getAttribute('data-target'));
      if (targetInput) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          targetInput.type = 'password';
          btn.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  // Enable Bootstrap tooltips if any
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
