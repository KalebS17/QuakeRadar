// Inicializa el mapa en San José, Costa Rica
const map = L.map('map', { zoomControl: false }).setView([9.9333, -84.0833], 13);
const earthquakeMarkers = L.layerGroup().addTo(map);

// Carga los tiles desde OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap',
}).addTo(map);

const redIcon = L.icon({
  iconUrl: '/static/images/AlfilerGif.gif',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -28],
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
document.getElementById('search-form').addEventListener('submit', function (e) {
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

let __didInitialFit = false;
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
    if (!__didInitialFit && bounds && L.latLngBounds(bounds).isValid()) {
      map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
      __didInitialFit = true;
    }
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

  filtered.sort((a, b) => b.mag - a.mag);

  earthquakeMarkers.clearLayers();
  addEarthquakeMarkers(filtered);

  filterPopup.style.display = 'none';
});

// Inicializar el mapa y cargar datos
(async function initMap() {
  const earthquakes = await fetchEarthquakeData();
  addEarthquakeMarkers(earthquakes);
})();

//Intervalo de refresco del mapa
const LIVE_UPDATE_INTERVAL_MS = 10000; // 10s (ajustable)

let _liveTimer = null;

//Funcion para refrescar los terremotos 
async function _refreshEarthquakesApplyingActiveFilters() {

  const earthquakes = await fetchEarthquakeData();

  // Reusar los filtros actuales si el usuario los tiene activos
  const dateInput = document.getElementById('filter-date');
  const magInput = document.getElementById('filter-magnitude');
  const locInput = document.getElementById('filter-location');
  const date = dateInput ? dateInput.value : '';
  const magnitude = magInput && magInput.value !== '' ? parseFloat(magInput.value) : NaN;
  const location = locInput ? locInput.value.trim().toLowerCase() : '';

  let filtered = earthquakes;
  if (date) filtered = filtered.filter(eq => new Date(eq.time) >= new Date(date));
  if (!isNaN(magnitude)) filtered = filtered.filter(eq => eq.mag >= magnitude);
  if (location) filtered = filtered.filter(eq => (eq.place || '').toLowerCase().includes(location));
  filtered.sort((a, b) => b.mag - a.mag);

  addEarthquakeMarkers(filtered);
}

//Funcion para arrancar actualizaciones en tiempo real
function startLiveUpdates() {
  if (_liveTimer !== null) return; 
  _liveTimer = setInterval(async () => {
    try {
      await _refreshEarthquakesApplyingActiveFilters();
    } catch (err) {
      console.error('Fallo al actualizar terremotos en tiempo real:', err);
    }
  }, LIVE_UPDATE_INTERVAL_MS);
}

//Funcion para detener actualizaciones en tiempo real
function stopLiveUpdates() {
  if (_liveTimer !== null) {
    clearInterval(_liveTimer);
    _liveTimer = null;
  }
}

// Pausar cuando la pestaña está oculta para ahorrar recursos
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopLiveUpdates();
  } else {
    startLiveUpdates();
    // actualización inmediata al volver
    _refreshEarthquakesApplyingActiveFilters().catch(console.error);
  }
});

// Arrancar inmediatamente
startLiveUpdates();
