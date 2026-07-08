const mapbox_token = 'pk.eyJ1Ijoic21hbGNhemEiLCJhIjoiY21yOWxsdGE1MXU1OTM0b20zb2lsZWF6bSJ9.4OpFI6JNjn9X1A3K0Dov5A'

const map = new mapboxgl.Map({
    accessToken: mapbox_token,
    container: 'map',
    // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
    style: 'mapbox://styles/mapbox/standard',
    center: [-98.5795, 39.8282],
    zoom: 5,
    attributionControl: false
});

const searchBox = new MapboxSearchBox();
searchBox.accessToken = mapbox_token;
searchBox.options = {
    language: 'en'
};
searchBox.mapboxgl = mapboxgl
searchBox.marker = true

map.addControl(searchBox)

const geolocate = new mapboxgl.GeolocateControl({
    positionOptions: {
        enableHighAccuracy: true
    },
    trackUserLocation: true,
    showUserHeading: true
});

map.addControl(geolocate);

const marker = new mapboxgl.Marker({
    draggable: true
})
    .setLngLat(map.getCenter())
    .addTo(map);

marker.on('dragend', () => {});

function geoLocateHelp(e) {
    const lngLat = {lng: e.coords.longitude, lat: e.coords.latitude};
    marker.setLngLat(lngLat);
}

geolocate.on('geolocate', geoLocateHelp);

geolocate.trigger();

function moveMarker() {
    marker.setLngLat(map.getCenter());
}

map.on('moveend', moveMarker);

//  grabs the marker's current position from the Mapbox object and copies it into the hidden inputs' value
const form = document.querySelector('form');
const latInput = document.getElementById('latitude');
const lngInput = document.getElementById('longitude');

form.addEventListener('submit', function () {
    const lngLat = marker.getLngLat();
    latInput.value = lngLat.lat;
    lngInput.value = lngLat.lng;
});
