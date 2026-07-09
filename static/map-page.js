const mapbox_token = 'pk.eyJ1Ijoic21hbGNhemEiLCJhIjoiY21yOWxsdGE1MXU1OTM0b20zb2lsZWF6bSJ9.4OpFI6JNjn9X1A3K0Dov5A'
const mapDiv = document.getElementById('map');
const lat = 39.8282;
const lng = -98.5795;

// sets up map for map page
const map = new mapboxgl.Map({
    accessToken: mapbox_token,
    container: 'map',
    style: 'mapbox://styles/mapbox/standard',
    center: [lng, lat],
    zoom: 4,
    attributionControl: false
});

// When the map loads fetches entry data from app.py
map.on('load', () => {
    fetch('/entries/locations')
    .then(res => res.json()) // parse into real JS object
    .then(entries => { // loops through each entry setting a marker for it
        entries.forEach(entry => {
            const marker = new mapboxgl.Marker()
                .setLngLat([entry.longitude, entry.latitude])
                .addTo(map);
            // reroutes to note page when a marker is clicked
            marker.getElement().addEventListener('click', () => {
                window.location.href = '/note?date=' + entry.date;
            })
        })
    })
    .catch(err => console.error('Failed to load entrys', err));
});
