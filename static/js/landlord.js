document.addEventListener('DOMContentLoaded', function () {
  // ---- Tabs (links still work without JS; this just avoids a reload) ----
  var tabs = document.querySelectorAll('.ld-tab');
  var panels = document.querySelectorAll('.ld-panel[data-panel]');

  function showTab(name) {
    tabs.forEach(function (t) { t.classList.toggle('is-active', t.dataset.tab === name); });
    panels.forEach(function (p) { p.classList.toggle('is-active', p.dataset.panel === name); });
    history.replaceState(null, '', '?tab=' + name);
  }

  if (panels.length) {
    document.querySelectorAll('[data-tab]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        showTab(link.dataset.tab);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  // ---- Province -> district dropdown ----
  var provinceSelect = document.getElementById('id_province');
  var districtSelect = document.getElementById('id_district');
  var dataEl = document.getElementById('province-districts');

  if (provinceSelect && districtSelect && dataEl) {
    var map = JSON.parse(dataEl.textContent);

    function fillDistricts(selected) {
      var districts = map[provinceSelect.value] || [];
      districtSelect.innerHTML = '';
      var blank = document.createElement('option');
      blank.value = '';
      blank.textContent = 'Select district';
      districtSelect.appendChild(blank);
      districts.forEach(function (d) {
        var opt = document.createElement('option');
        opt.value = d;
        opt.textContent = d;
        if (d === selected) opt.selected = true;
        districtSelect.appendChild(opt);
      });
    }

    fillDistricts(districtSelect.dataset.selected || '');
    provinceSelect.addEventListener('change', function () { fillDistricts(''); });
  }
});