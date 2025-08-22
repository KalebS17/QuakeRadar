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
// Obtener datos de terremotos (opcionalmente por rango de fechas)
async function fetchEarthquakeData(dateFrom, dateTo) {
  let url = '/fetch_earthquake_data/';
  if (dateFrom && dateTo) {
    url += `?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`;
  }
  const response = await fetch(url);
  const data = await response.json();
  return data.earthquakes;
}

let __didInitialFit = false;
// Agregar marcadores al mapa
function addEarthquakeMarkers(earthquakes) {
  earthquakeMarkers.clearLayers();
  const bounds = [];

  // Función para escapar HTML especial
  function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/[&<>"']/g, function (c) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]);
    });
  }
  earthquakes.forEach(earthquake => {
    const [lon, lat, depth] = earthquake.coordinates;
    // Formatear fecha y hora
    let fechaHora = '';
    if (earthquake.time) {
      try {
        const dateObj = new Date(earthquake.time);
        fechaHora = dateObj.toLocaleString('es-CR', { hour12: false });
      } catch (e) {
        fechaHora = escapeHTML(earthquake.time);
      }
    }
    const marker = L.marker([lat, lon], { icon: redIcon });
    marker.bindPopup(`
      <strong>Detalles del terremoto:</strong><br>
      ID: ${escapeHTML(earthquake.id)}<br>
      Magnitud: ${escapeHTML(earthquake.mag)}<br>
      Lugar: ${escapeHTML(earthquake.place)}<br>
      Tipo: ${escapeHTML(earthquake.type)}<br>
      Profundidad: ${escapeHTML(depth)} km<br>
      <span><strong>Fecha y hora:</strong> ${fechaHora}</span>
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

  const dateFrom = document.getElementById('filter-date-from').value;
  const dateTo = document.getElementById('filter-date-to').value;
  const magnitude = parseFloat(document.getElementById('filter-magnitude').value);
  const location = document.getElementById('filter-location').value.toLowerCase();

  // Validación de fechas
  if (dateFrom && dateTo) {
    const from = new Date(dateFrom);
    const to = new Date(dateTo);
    const diffDays = (to - from) / (1000 * 60 * 60 * 24);
    if (from > to) {
      alert('La fecha "Desde" no puede ser mayor que la fecha "Hasta".');
      return;
    }
    if (diffDays > 3) {
      alert('El rango máximo permitido es de 3 días.');
      return;
    }
  }

  // Llamar a la API con el rango de fechas si se especifica
  let earthquakes = [];
  if (dateFrom && dateTo) {
    earthquakes = await fetchEarthquakeData(dateFrom, dateTo);
  } else {
    earthquakes = await fetchEarthquakeData();
  }

  let filtered = earthquakes;
  if (!isNaN(magnitude)) filtered = filtered.filter(eq => eq.mag >= magnitude);
  if (location) filtered = filtered.filter(eq => (eq.place || '').toLowerCase().includes(location));
  filtered.sort((a, b) => b.mag - a.mag);

  earthquakeMarkers.clearLayers();
  addEarthquakeMarkers(filtered);
  filterPopup.style.display = 'none';
});

// Botón para limpiar filtros y volver a la vista por defecto
document.getElementById('clear-filters-btn').addEventListener('click', async () => {
  document.getElementById('filter-date-from').value = '';
  document.getElementById('filter-date-to').value = '';
  document.getElementById('filter-magnitude').value = '';
  document.getElementById('filter-location').value = '';
  // Cargar sismos del último día
  const earthquakes = await fetchEarthquakeData();
  earthquakeMarkers.clearLayers();
  addEarthquakeMarkers(earthquakes);
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

  // Leer filtros activos
  const dateFromInput = document.getElementById('filter-date-from');
  const dateToInput = document.getElementById('filter-date-to');
  const magInput = document.getElementById('filter-magnitude');
  const locInput = document.getElementById('filter-location');
  const dateFrom = dateFromInput ? dateFromInput.value : '';
  const dateTo = dateToInput ? dateToInput.value : '';
  const magnitude = magInput && magInput.value !== '' ? parseFloat(magInput.value) : NaN;
  const location = locInput ? locInput.value.trim().toLowerCase() : '';

  let earthquakes = [];
  if (dateFrom && dateTo) {
    earthquakes = await fetchEarthquakeData(dateFrom, dateTo);
  } else {
    earthquakes = await fetchEarthquakeData();
  }

  let filtered = earthquakes;
  if (dateFrom && dateTo) {
    const from = new Date(dateFrom);
    const to = new Date(dateTo);
    filtered = filtered.filter(eq => {
      const eqDate = new Date(eq.time);
      return eqDate >= from && eqDate <= to;
    });
  }
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
