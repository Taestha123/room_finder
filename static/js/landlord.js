
document.addEventListener('DOMContentLoaded', function () {

  // Dashboard tabs
  var tabs = document.querySelectorAll('.ld-tab[data-tab]');
  var panels = document.querySelectorAll('.ld-panel[data-panel]');

  function showTab(name) {
    tabs.forEach(function (tab) {
      tab.classList.toggle('is-active', tab.dataset.tab === name);
    });

    panels.forEach(function (panel) {
      panel.classList.toggle('is-active', panel.dataset.panel === name);
    });

    history.replaceState(null, '', '?tab=' + name);
  }

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function (event) {
      event.preventDefault();
      showTab(tab.dataset.tab);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });


  // Province -> District dropdown
  var province = document.getElementById('id_province');
  var district = document.getElementById('id_district');
  var data = document.getElementById('province-districts');

  if (province && district && data) {
    var districtMap = JSON.parse(data.textContent);

    function fillDistricts(selected) {
      district.innerHTML = '<option value="">Select...</option>';

      (districtMap[province.value] || []).forEach(function (name) {
        var option = document.createElement('option');
        option.value = name;
        option.textContent = name;

        if (name === selected) {
          option.selected = true;
        }

        district.appendChild(option);
      });
    }

    var selectedDistrict = district.dataset.selected || district.value;

    fillDistricts(selectedDistrict);

    province.addEventListener('change', function () {
      fillDistricts('');
    });
  }


  // Add Listing Wizard
  var form = document.querySelector('form.listing-wizard');

  if (form) {
    var pages = form.querySelectorAll('.listing-wizard-page');
    var steps = form.querySelectorAll('.listing-step');
    var current = 1;

    function review() {

      form.querySelectorAll('[data-review]').forEach(function (target) {
        var source = form.querySelector('[name="' + target.dataset.review + '"]');

        if (!source) return;

        target.textContent = source.tagName === 'SELECT'
          ? (source.selectedOptions[0] ? source.selectedOptions[0].textContent : 'Not provided')
          : (source.value || 'Not provided');
      });

      var included = [];

      [['bills_water', 'Water'],
       ['bills_electricity', 'Electricity'],
       ['bills_internet', 'Internet']].forEach(function (item) {

        var checkbox = form.querySelector('[name="' + item[0] + '"]');

        if (checkbox && checkbox.checked) {
          included.push(item[1]);
        }
      });

      var bills = document.getElementById('review-bills');

      if (bills) {
        bills.textContent = included.length
          ? included.join(', ')
          : 'No bills included';
      }

      var pinText = document.getElementById('review-map-pin');

      if (pinText) {
        var latitude = form.querySelector('[name="latitude"]');
        var longitude = form.querySelector('[name="longitude"]');

        pinText.textContent = latitude && longitude && latitude.value && longitude.value
          ? latitude.value + ', ' + longitude.value
          : 'Not provided';
      }

      var furnished = form.querySelector('[name="furnished_status"]');
      var furnishedReview = form.querySelector('[data-review-facility="furnished_status"]');

      if (furnishedReview) {
        furnishedReview.textContent = furnished && furnished.selectedOptions.length
          ? furnished.selectedOptions[0].textContent
          : 'Not provided';
      }

      var facilityNames = [];

      form.querySelectorAll('.ld-facility-grid input[type="checkbox"]').forEach(function (checkbox) {
        if (checkbox.checked) {
          var label = checkbox.closest('label');

          if (label) {
            facilityNames.push(
              label.querySelector('span')
                ? label.querySelector('span').textContent.trim()
                : label.textContent.trim()
            );
          }
        }
      });

      var facilitiesReview = document.getElementById('review-facilities');

      if (facilitiesReview) {
        facilitiesReview.textContent = facilityNames.length
          ? facilityNames.join(', ')
          : 'None selected';
      }
    }


    function showStep(number) {
      current = number;

      pages.forEach(function (page) {
        var active = Number(page.dataset.page) === number;

        page.hidden = !active;
        page.classList.toggle('active', active);
      });

      steps.forEach(function (step) {
        var n = Number(step.dataset.step);

        step.classList.toggle('is-active', n === number);
        step.classList.toggle('is-complete', n < number);
      });

      if (number === 5) {
        review();
      }

      window.scrollTo({ top: 0, behavior: 'smooth' });
    }


    // Next buttons with validation
    form.querySelectorAll('[data-next]').forEach(function (button) {
  button.addEventListener('click', function () {

    var page = form.querySelector(
      '.listing-wizard-page[data-page="' + current + '"]'
    );

    if (!page) return;

    // Check required fields in the current step only
    var fields = page.querySelectorAll(
      'input[required], select[required], textarea[required]'
    );

    for (var i = 0; i < fields.length; i++) {
      if (!fields[i].checkValidity()) {
        fields[i].reportValidity();
        fields[i].focus();
        return;
      }
    }

    if (current < 5) {
      showStep(current + 1);
    }
  });
});

    // Previous buttons
    form.querySelectorAll('[data-back]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (current > 1) {
          showStep(current - 1);
        }
      });
    });

    showStep(1);
  }


  // Google Maps Pin -> Latitude and Longitude
  var pin = document.getElementById('google_maps_pin');
  var lat = document.getElementById('id_latitude');
  var lng = document.getElementById('id_longitude');
  var status = document.getElementById('map-pin-status');

  if (pin && lat && lng) {

    function parsePin(value) {

      var patterns = [
        /@(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)/,
        /!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)/,
        /[?&](?:q|query|ll|center)=(-?\d{1,2}\.\d+)[,%20]+(-?\d{1,3}\.\d+)/,
        /^\s*(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)\s*$/
      ];

      for (var i = 0; i < patterns.length; i++) {
        var match = value.match(patterns[i]);

        if (match) {
          var a = Number(match[1]);
          var b = Number(match[2]);

          if (a >= -90 && a <= 90 && b >= -180 && b <= 180) {
            return {
              latitude: a.toFixed(6),
              longitude: b.toFixed(6)
            };
          }
        }
      }

      return null;
    }


    function updatePin() {
      var coords = parsePin(pin.value.trim());

      if (coords) {
        lat.value = coords.latitude;
        lng.value = coords.longitude;

        status.textContent = '✓ Map pin coordinates added.';
        status.classList.add('is-valid');
        status.classList.remove('is-error');

      } else {
        lat.value = '';
        lng.value = '';

        status.textContent = pin.value.trim()
          ? 'Could not read coordinates. Paste a Google Maps link with a dropped pin, or enter latitude, longitude.'
          : '';

        status.classList.remove('is-valid');
        status.classList.toggle('is-error', !!pin.value.trim());
      }
    }

    pin.addEventListener('input', updatePin);
    pin.addEventListener('change', updatePin);
  }

});
