const coordinates = document.getElementById('coordinates');

const map = new mapboxgl.Map({
    accessToken: 'pk.eyJ1Ijoic21hbGNhemEiLCJhIjoiY21yM3dzY3hoMDV2MTMzb21paDFoOHp6bSJ9.cIrFL02wGGG7edLxGqOaHA',
    container: 'map',
    // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
    style: 'mapbox://styles/mapbox/standard',
    center: [-98.5795, 39.8282],
    zoom: 5,
    attributionControl: false
});

const searchBox = new MapboxSearchBox();
searchBox.accessToken = 'pk.eyJ1Ijoic21hbGNhemEiLCJhIjoiY21yM3dzY3hoMDV2MTMzb21paDFoOHp6bSJ9.cIrFL02wGGG7edLxGqOaHA';
searchBox.options = {
    language: 'en'
}
searchBox.mapboxgl = mapboxgl
searchBox.marker = true

map.addControl(searchBox)

const geolocate = new mapboxgl.GeolocateControl({
    positionOptions: {
        enableHighAccuracy: true
    },
    trackUserLocation: true,
    showUserHeading: true
})

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

document.getElementById("saveBtn").addEventListener("click", function() { 
    const lngLat = marker.getLngLat();

    const data = {
        latitude: lngLat.lat,
        longitude: lngLat.lng
    };

    fetch('/save-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => console.log('Saved:', result))
    .catch(err => console.error('Save failed:', err));

});
