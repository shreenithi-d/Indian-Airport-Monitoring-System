// Interactive Leaflet Map for Indian Airports
let airportMap = null;
let markersLayer = null;
let allAirportsData = [];
let routePolyline = null;

function initIndianAirportMap(mapElementId, initialAirports, selectedAirportId = null) {
  const mapContainer = document.getElementById(mapElementId);
  if (!mapContainer) return;

  // Initialize map centered on central India
  airportMap = L.map(mapElementId, {
    center: [22.3511148, 78.6677428],
    zoom: 5,
    minZoom: 4,
    maxZoom: 14,
    scrollWheelZoom: true
  });

  // OpenStreetMap Tile Layer
  const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Indian Airport Monitoring System'
  });

  tileLayer.addTo(airportMap);

  // Check tile loading failure
  tileLayer.on('tileerror', function () {
    const errorBanner = document.getElementById('map-error-banner');
    if (errorBanner) {
      errorBanner.classList.remove('d-none');
    }
  });

  markersLayer = L.layerGroup().addTo(airportMap);
  allAirportsData = initialAirports || [];

  renderAirportMarkers(allAirportsData);

  // Pre-select if specified
  if (selectedAirportId) {
    focusOnAirport(selectedAirportId);
  }

  // Setup search and filter listeners
  setupMapFilterListeners();
}

function getMarkerPinClass(category) {
  if (category === 'International') return 'pin-international';
  if (category === 'Customs') return 'pin-customs';
  if (category === 'Domestic') return 'pin-domestic';
  return 'pin-development';
}

function renderAirportMarkers(airports) {
  if (!markersLayer) return;
  markersLayer.clearLayers();

  airports.forEach(airport => {
    if (!airport.latitude || !airport.longitude) return;

    const pinClass = getMarkerPinClass(airport.category);
    const customIcon = L.divIcon({
      className: 'custom-leaflet-pin',
      html: `<div class="custom-airport-pin ${pinClass}"><i class="bi bi-airplane-engines-fill"></i></div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16]
    });

    const marker = L.marker([airport.latitude, airport.longitude], { icon: customIcon });

    // Popup content
    const iataBadge = airport.iata_code && airport.iata_code !== 'N/A' 
      ? `<span class="popup-badge-code">${airport.iata_code}</span>` 
      : `<span class="popup-badge-code">${airport.icao_code || 'IN'}</span>`;

    const popupHtml = `
      <div class="popup-airport-card">
        <div class="d-flex justify-content-between align-items-start popup-airport-header">
          <div>
            <h6 class="popup-airport-title">${airport.name}</h6>
            <p class="popup-airport-sub"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${airport.city}, ${airport.state}</p>
          </div>
          ${iataBadge}
        </div>
        <div class="d-flex gap-1 mb-2">
          <span class="badge badge-${airport.category ? airport.category.toLowerCase() : 'domestic'}">${airport.category}</span>
          <span class="badge badge-${airport.operational_status === 'Operational' ? 'operational' : 'non-operational'}">${airport.operational_status}</span>
        </div>
        <div class="popup-stat-grid">
          <div class="popup-stat-box">
            <div class="popup-stat-num">${airport.departures_count || 0}</div>
            <div class="popup-stat-label">Departures</div>
          </div>
          <div class="popup-stat-box">
            <div class="popup-stat-num">${airport.arrivals_count || 0}</div>
            <div class="popup-stat-label">Arrivals</div>
          </div>
        </div>
        <div class="d-grid gap-1 mt-2">
          <a href="/airports/${airport.id}" class="btn btn-sm btn-aviation-primary">
            <i class="bi bi-info-circle me-1"></i>View Airport Details
          </a>
          <a href="/flights/search?origin_id=${airport.id}" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-search me-1"></i>Find Departing Flights
          </a>
        </div>
      </div>
    `;

    marker.bindPopup(popupHtml);
    marker.airportId = airport.id;
    markersLayer.addLayer(marker);
  });
}

function focusOnAirport(airportId) {
  const airport = allAirportsData.find(a => a.id === parseInt(airportId));
  if (airport && airportMap) {
    airportMap.flyTo([airport.latitude, airport.longitude], 10, {
      duration: 1.2
    });

    // Find and open popup
    markersLayer.eachLayer(layer => {
      if (layer.airportId === airport.id) {
        setTimeout(() => layer.openPopup(), 1200);
      }
    });
  }
}

function setupMapFilterListeners() {
  const searchInput = document.getElementById('map-search-input');
  const stateSelect = document.getElementById('map-state-filter');
  const catSelect = document.getElementById('map-category-filter');
  const statusSelect = document.getElementById('map-status-filter');
  const resetBtn = document.getElementById('map-reset-btn');

  function applyFilters() {
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const selectedState = stateSelect ? stateSelect.value : 'All';
    const selectedCat = catSelect ? catSelect.value : 'All';
    const selectedStatus = statusSelect ? statusSelect.value : 'All';

    const filtered = allAirportsData.filter(a => {
      const matchSearch = !searchTerm ||
        a.name.toLowerCase().includes(searchTerm) ||
        a.city.toLowerCase().includes(searchTerm) ||
        (a.iata_code && a.iata_code.toLowerCase().includes(searchTerm)) ||
        (a.icao_code && a.icao_code.toLowerCase().includes(searchTerm));

      const matchState = (selectedState === 'All' || a.state === selectedState);
      const matchCat = (selectedCat === 'All' || a.category === selectedCat);
      const matchStatus = (selectedStatus === 'All' || a.operational_status === selectedStatus);

      return matchSearch && matchState && matchCat && matchStatus;
    });

    renderAirportMarkers(filtered);

    // Update count display
    const countEl = document.getElementById('visible-airports-count');
    if (countEl) {
      countEl.innerText = filtered.length;
    }
  }

  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (stateSelect) stateSelect.addEventListener('change', applyFilters);
  if (catSelect) catSelect.addEventListener('change', applyFilters);
  if (statusSelect) statusSelect.addEventListener('change', applyFilters);

  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      if (searchInput) searchInput.value = '';
      if (stateSelect) stateSelect.value = 'All';
      if (catSelect) catSelect.value = 'All';
      if (statusSelect) statusSelect.value = 'All';
      applyFilters();
      airportMap.flyTo([22.3511148, 78.6677428], 5);
    });
  }
}

// Function to draw illustrative scheduled route between two airports
function drawFlightRoute(originLat, originLng, destLat, destLng, flightLabel) {
  if (!airportMap) return;

  if (routePolyline) {
    airportMap.removeLayer(routePolyline);
  }

  const latlngs = [
    [originLat, originLng],
    [destLat, destLng]
  ];

  routePolyline = L.polyline(latlngs, {
    color: '#1769FF',
    weight: 3,
    opacity: 0.85,
    dashArray: '8, 8',
    smoothFactor: 1
  }).addTo(airportMap);

  if (flightLabel) {
    routePolyline.bindTooltip(flightLabel, { permanent: true, direction: 'center' });
  }

  airportMap.fitBounds(routePolyline.getBounds(), { padding: [50, 50] });
}
