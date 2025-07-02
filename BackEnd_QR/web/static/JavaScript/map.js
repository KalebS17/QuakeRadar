// Inicializa el mapa en San José, Costa Rica
const map = L.map('map', { zoomControl: false }).setView([9.9333, -84.0833], 13);


// Carga los tiles desde OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap',
}).addTo(map);

// Funciones para botones
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

// Barra de búsqueda con Nominatim
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


