// Flight Search Form Validation & Interactions
document.addEventListener('DOMContentLoaded', function () {
  const originSelect = document.getElementById('search-origin');
  const destSelect = document.getElementById('search-dest');
  const swapBtn = document.getElementById('swap-airports-btn');
  const searchForm = document.getElementById('flight-search-form');
  const departureDateInput = document.getElementById('search-date');

  // Prevent past dates
  if (departureDateInput) {
    const today = new Date().toISOString().split('T')[0];
    departureDateInput.min = today;
  }

  // Swap airports
  if (swapBtn && originSelect && destSelect) {
    swapBtn.addEventListener('click', function () {
      const temp = originSelect.value;
      originSelect.value = destSelect.value;
      destSelect.value = temp;
    });
  }

  // Form submission validation
  if (searchForm) {
    searchForm.addEventListener('submit', function (e) {
      if (originSelect && destSelect) {
        if (originSelect.value && destSelect.value && originSelect.value === destSelect.value) {
          e.preventDefault();
          alert("Origin and destination airport cannot be the same! Please select two different airports.");
        }
      }
    });
  }
});
