// Inicializa el mapa en San José, Costa Rica
const map = L.map('map').setView([9.9333, -84.0833], 13);

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


