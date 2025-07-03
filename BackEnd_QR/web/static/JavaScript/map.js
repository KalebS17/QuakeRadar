// Inicializa el mapa en San José, Costa Rica
const map = L.map('map', { zoomControl: false }).setView([9.9333, -84.0833], 13);
const earthquakeMarkers = L.layerGroup().addTo(map);

// Carga los tiles desde OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap',
}).addTo(map);

const redIcon = L.icon({
  iconUrl: '/static/images/location.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// Funciones de botones
function zoomIn() {
  map.zoomIn();
}

function zoomOut() {
  map.zoomOut();
}

function locateUser() {
  map.locate({ setView: true, maxZoom: 16 });
}

map.on('locationfound', function (e) {
  L.marker(e.latlng).addTo(map).bindPopup('¡Estás aquí!').openPopup();
});

map.on('locationerror', function () {
  alert('No se pudo obtener tu ubicación');
});

// Búsqueda con Nominatim
document.getElementById('search-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const query = document.getElementById('search-input').value;
  if (!query) return;
  fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`)
    .then(res => res.json())
    .then(data => {
      if (data && data.length > 0) {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);
        map.setView([lat, lon], 15);
        L.marker([lat, lon]).addTo(map).bindPopup(data[0].display_name).openPopup();
      } else {
        alert('No se encontró la ubicación.');
      }
    })
    .catch(() => alert('Error al buscar la ubicación.'));
});

// Obtener datos de terremotos
async function fetchEarthquakeData() {
  const response = await fetch('/fetch_earthquake_data/');
  const data = await response.json();
  return data.earthquakes;
}

// Agregar marcadores al mapa
function addEarthquakeMarkers(earthquakes) {
  earthquakeMarkers.clearLayers();
  const bounds = [];

  earthquakes.forEach(earthquake => {
    const [lon, lat, depth] = earthquake.coordinates;
    const marker = L.marker([lat, lon], { icon: redIcon });
    marker.bindPopup(`
      <strong>Detalles del terremoto:</strong><br>
      ID: ${earthquake.id}<br>
      Magnitud: ${earthquake.mag}<br>
      Lugar: ${earthquake.place}<br>
      Tipo: ${earthquake.type}<br>
      Profundidad: ${depth} km<br>
    `);
    earthquakeMarkers.addLayer(marker);
    bounds.push([lat, lon]);
  });

  if (bounds.length > 0) {
    map.fitBounds(bounds);
  }
}

// Botón menú y popup filtros
const menuToggle = document.getElementById('menu-toggle');
const filterPopup = document.getElementById('filter-popup');

menuToggle.addEventListener('click', (e) => {
  e.stopPropagation();
  if (filterPopup.style.display === 'block') {
    filterPopup.style.display = 'none';
  } else {
    filterPopup.style.display = 'block';
  }
});

document.addEventListener('click', (e) => {
  if (!filterPopup.contains(e.target) && !menuToggle.contains(e.target)) {
    filterPopup.style.display = 'none';
  }
});

// Aplicar filtros en el popup
document.getElementById('filter-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const date = document.getElementById('filter-date').value;
  const magnitude = parseFloat(document.getElementById('filter-magnitude').value);
  const location = document.getElementById('filter-location').value.toLowerCase();

  const earthquakes = await fetchEarthquakeData();

  let filtered = earthquakes;

  if (date) filtered = filtered.filter(eq => new Date(eq.time) >= new Date(date));
  if (!isNaN(magnitude)) filtered = filtered.filter(eq => eq.mag >= magnitude);
  if (location) filtered = filtered.filter(eq => eq.place.toLowerCase().includes(location));

  filtered.sort((a,b) => b.mag - a.mag);

  earthquakeMarkers.clearLayers();
  addEarthquakeMarkers(filtered);

  filterPopup.style.display = 'none';
});

// Inicializar el mapa y cargar datos
(async function initMap() {
  const earthquakes = await fetchEarthquakeData();
  addEarthquakeMarkers(earthquakes);
})();