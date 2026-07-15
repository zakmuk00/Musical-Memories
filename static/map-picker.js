// Grab the map element from the HTML
const mapElement = document.getElementById('map');

// Read the token value we stored in the data-token attribute
const mapboxToken = mapElement.dataset.token;

// Creates Mapbox map
const map = new mapboxgl.Map({
  accessToken: mapboxToken,
  container: "map",
  // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
  style: "mapbox://styles/mapbox/standard",
  center: [-98.5795, 39.8282],
  zoom: 5,
  attributionControl: false,
});

// Creates and adds a search box for Map
const searchBox = new MapboxSearchBox();
searchBox.accessToken = mapboxToken;
searchBox.options = {
  language: "en",
};
searchBox.mapboxgl = mapboxgl;
searchBox.marker = false;
map.addControl(searchBox);

// Creates and adds a Geolocate button to navigate to users current location
const geolocate = new mapboxgl.GeolocateControl({
  positionOptions: {
    enableHighAccuracy: true,
  },
  trackUserLocation: true,
  showUserHeading: true,
});
map.addControl(geolocate);

// Creates a marker at the center of the map
const marker = new mapboxgl.Marker({
  draggable: true,
})
  .setLngLat(map.getCenter())
  .addTo(map);

// Moves Marker to the new center when the user moves the map
marker.on("dragend", () => {});
function geoLocateHelp(e) {
  const lngLat = { lng: e.coords.longitude, lat: e.coords.latitude };
  marker.setLngLat(lngLat);
}
geolocate.on("geolocate", geoLocateHelp);
geolocate.trigger();
function moveMarker() {
  marker.setLngLat(map.getCenter());
}
map.on("moveend", moveMarker);

//  grabs the marker's current position from the Mapbox object and copies it into the hidden inputs' value
const form = document.querySelector("form");
const latInput = document.getElementById("latitude");
const lngInput = document.getElementById("longitude");

form.addEventListener("submit", function () {
  const lngLat = marker.getLngLat();
  latInput.value = lngLat.lat;
  lngInput.value = lngLat.lng;
});