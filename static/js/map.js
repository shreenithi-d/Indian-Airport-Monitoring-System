// =========================
// LOAD AIRPORT DATA
// =========================

const airportsData = JSON.parse(
    document.getElementById("airport-data").textContent
);


// =========================
// CREATE MAP
// =========================

const map = L.map("map").setView(
    [22.9734, 78.6569],
    5
);


// =========================
// SATELLITE MAP
// =========================

L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    {
        attribution: "Esri Satellite"
    }
).addTo(map);


// =========================
// AIRPLANE ICON
// =========================

const airplaneMarker = L.divIcon({

    html: `
        <div style="
            font-size:32px;
            color:#00c6ff;
            text-shadow:
            0 0 10px white,
            0 0 20px white;
        ">
            <i class="fas fa-plane"></i>
        </div>
    `,

    className: "",

    iconSize: [40, 40],

    iconAnchor: [20, 20]

});


// =========================
// AIRPORT MARKERS
// =========================

Object.values(airportsData).forEach((airport) => {

    const popupContent = `

        <div class="popup-card">

            <img
                src="${airport.image}"
                alt="${airport.name}"
                style="
                    width:100%;
                    height:150px;
                    object-fit:cover;
                    border-radius:10px;
                ">

            <h5 class="mt-2">
                ${airport.name}
            </h5>

            <p>
                <strong>City:</strong>
                ${airport.city}
            </p>

            <p>
                ${airport.description}
            </p>

            <div class="d-grid">

                <a href="/airport/${airport.code}"
                   class="btn btn-primary">

                    See More

                </a>

            </div>

        </div>

    `;

    L.marker(
        [airport.lat, airport.lng],
        {
            icon: airplaneMarker
        }
    )
    .addTo(map)
    .bindPopup(
        popupContent,
        {
            maxWidth: 320
        }
    );

});


// =========================
// INDIA BOUNDS
// =========================

const indiaBounds = [

    [6.0, 68.0],

    [37.5, 97.5]

];

map.setMaxBounds(indiaBounds);

map.fitBounds(indiaBounds);


// =========================
// ENABLE MAP FEATURES
// =========================

map.scrollWheelZoom.enable();

map.doubleClickZoom.enable();

map.dragging.enable();

map.touchZoom.enable();

map.boxZoom.enable();

map.keyboard.enable();


// =========================
// ZOOM EVENT
// =========================

map.on("zoomend", function () {

    console.log(
        "Current Zoom:",
        map.getZoom()
    );

});


// =========================
// SUCCESS
// =========================

console.log(
    "Indian Airport Monitoring System Loaded Successfully"
);