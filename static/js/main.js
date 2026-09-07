document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn = document.querySelector('.navbar-toggle');
  var mobileMenu = document.querySelector('.navbar-mobile-menu');

  if (toggleBtn && mobileMenu) {
    toggleBtn.addEventListener('click', function () {
      mobileMenu.classList.toggle('open');
    });
  }
});