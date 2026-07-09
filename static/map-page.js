const mapbox_token = 'pk.eyJ1Ijoic21hbGNhemEiLCJhIjoiY21yOWxsdGE1MXU1OTM0b20zb2lsZWF6bSJ9.4OpFI6JNjn9X1A3K0Dov5A'
const mapDiv = document.getElementById('map');
const lat = 39.8282;
const lng = -98.5795;

const map = new mapboxgl.Map({
    accessToken: mapbox_token,
    container: 'map',
    style: 'mapbox://styles/mapbox/standard',
    center: [lng, lat],
    zoom: 4,
    attributionControl: false
});

map.on('load', () => {
    fetch('/entries/locations')
    .then(res => res.json()) // parse into real JS object
    .then(entries => {
        entries.forEach(entry => {
            const marker = new mapboxgl.Marker()
                .setLngLat([entry.longitude, entry.latitude])
                .addTo(map);
            
            marker.getElement().addEventListener('click', () => {
                window.location.href = '/note';
            })
        })
    })
    .catch(err => console.error('Failed to load entrys', err));
});
