document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn = document.querySelector('.navbar-toggle');
  var mobileMenu = document.querySelector('.navbar-mobile-menu');

  if (toggleBtn && mobileMenu) {
    toggleBtn.addEventListener('click', function () {
      mobileMenu.classList.toggle('open');
    });
  }
  document.querySelectorAll('.logout-link').forEach(function (link) {
  link.addEventListener('click', function (e) {
    if (!confirm('Are you sure you want to log out?')) {
      e.preventDefault();
    }
  });
});
});