// Interactive Aircraft Seat Selection Logic
document.addEventListener('DOMContentLoaded', function () {
  const seatButtons = document.querySelectorAll('.aircraft-seat-btn');
  const requiredCountEl = document.getElementById('required-passengers-count');
  const selectedCountEl = document.getElementById('selected-seats-count');
  const selectedCodesEl = document.getElementById('selected-seat-codes');
  const seatChargesTotalEl = document.getElementById('seat-charges-total');
  const grandTotalEl = document.getElementById('grand-total-amount');
  const proceedBtn = document.getElementById('proceed-to-passengers-btn');
  const hiddenSeatIdsInput = document.getElementById('hidden-seat-ids');
  
  if (!requiredCountEl) return;

  const requiredCount = parseInt(requiredCountEl.innerText) || 1;
  const baseFarePerPax = parseFloat(document.getElementById('base-fare-per-pax')?.value || 0);

  let selectedSeats = []; // { id, code, charge }

  seatButtons.forEach(button => {
    button.addEventListener('click', function () {
      const isAvailable = this.classList.contains('seat-state-available');
      const isSelected = this.classList.contains('seat-state-selected');

      // Do nothing if seat is occupied, held, or restricted
      if (!isAvailable && !isSelected) {
        return;
      }

      const seatId = parseInt(this.getAttribute('data-seat-id'));
      const seatCode = this.getAttribute('data-seat-code');
      const seatCharge = parseFloat(this.getAttribute('data-seat-charge') || 0);

      if (isSelected) {
        // Deselect seat
        this.classList.remove('seat-state-selected');
        this.classList.add('seat-state-available');
        selectedSeats = selectedSeats.filter(s => s.id !== seatId);
      } else {
        // Check if limit reached
        if (selectedSeats.length >= requiredCount) {
          alert(`You can select a maximum of ${requiredCount} seat(s) for this booking.`);
          return;
        }

        // Select seat
        this.classList.remove('seat-state-available');
        this.classList.add('seat-state-selected');
        selectedSeats.push({ id: seatId, code: seatCode, charge: seatCharge });
      }

      updateSeatSummary();
    });
  });

  function updateSeatSummary() {
    if (selectedCountEl) {
      selectedCountEl.innerText = selectedSeats.length;
    }

    if (selectedCodesEl) {
      if (selectedSeats.length === 0) {
        selectedCodesEl.innerHTML = '<span class="text-muted">None selected yet</span>';
      } else {
        selectedCodesEl.innerHTML = selectedSeats.map(s => 
          `<span class="badge bg-primary me-1 px-2 py-1">${s.code}</span>`
        ).join(' ');
      }
    }

    // Calculate totals
    const seatChargesSum = selectedSeats.reduce((acc, curr) => acc + curr.charge, 0);
    const baseFareTotal = baseFarePerPax * requiredCount;
    const taxes = (baseFareTotal + seatChargesSum) * 0.05 + (250 * requiredCount);
    const grandTotal = baseFareTotal + seatChargesSum + taxes;

    if (seatChargesTotalEl) {
      seatChargesTotalEl.innerText = `₹${seatChargesSum.toFixed(2)}`;
    }
    if (grandTotalEl) {
      grandTotalEl.innerText = `₹${grandTotal.toFixed(2)}`;
    }

    // Update hidden input for form submission
    if (hiddenSeatIdsInput) {
      hiddenSeatIdsInput.value = selectedSeats.map(s => s.id).join(',');
    }

    // Enable/disable proceed button
    if (proceedBtn) {
      if (selectedSeats.length === requiredCount) {
        proceedBtn.removeAttribute('disabled');
        proceedBtn.classList.remove('btn-secondary');
        proceedBtn.classList.add('btn-aviation-primary');
        proceedBtn.innerHTML = `Continue to Passenger Details (${selectedSeats.length}/${requiredCount}) <i class="bi bi-arrow-right ms-1"></i>`;
      } else {
        proceedBtn.setAttribute('disabled', 'disabled');
        proceedBtn.classList.remove('btn-aviation-primary');
        proceedBtn.classList.add('btn-secondary');
        proceedBtn.innerHTML = `Select ${requiredCount - selectedSeats.length} more seat(s) to continue`;
      }
    }
  }
});
