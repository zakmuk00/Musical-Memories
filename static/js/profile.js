let friendMap = null;
let friendMarkers = [];

function getMapStyle() {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    return isDark ? 'mapbox://styles/mapbox/dark-v11' : 'mapbox://styles/mapbox/streets-v12';
}

document.addEventListener('DOMContentLoaded', function () {
    const friendModalEl = document.getElementById('friendPreviewModal');

    friendModalEl.addEventListener('show.bs.modal', function (event) {
        const triggerButton = event.relatedTarget;
        const username = triggerButton.getAttribute('data-username');
        
        document.getElementById('modal-friend-username').textContent = username;
        
        const calContainer = document.getElementById('friend-calendar-container');
        calContainer.innerHTML = `<div class="spinner-border spinner-border-sm" role="status"></div> Loading...`;

        fetch(`/api/user/${username}/preview-data`)
            .then(res => res.json())
            .then(data => {
                if (!data.events || data.events.length === 0) {
                    calContainer.innerHTML = '<p class="text-muted small">No calendar entries recorded yet.</p>';
                } else {
                    let html = '';
                    data.events.slice(0, 10).forEach(evt => {
                        html += `
                            <div class="mini-calendar-item d-flex align-items-center justify-content-between">
                                <div>
                                    <div class="fw-bold small">${evt.title || 'Untitled'}</div>
                                    <div class="text-muted extra-small" style="font-size: 0.75rem;">${evt.artist || ''}</div>
                                </div>
                                <span class="badge mini-calendar-badge">${evt.date}</span>
                            </div>
                        `;
                    });
                    calContainer.innerHTML = html;
                }

                initFriendMap(data.locations);
            })
            .catch(err => {
                console.error("Error loading friend preview:", err);
                calContainer.innerHTML = '<p class="text-danger small">Failed to load friend data.</p>';
            });
    });

    friendModalEl.addEventListener('shown.bs.modal', function () {
        if (friendMap) {
            friendMap.resize();
        }
    });

    const themeObserver = new MutationObserver(() => {
        if (friendMap) {
            friendMap.setStyle(getMapStyle());
        }
    });
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme']
    });
});

function initFriendMap(locations) {
    if (!MAPBOX_TOKEN) {
        document.getElementById('friend-map').innerHTML = 
            '<div class="p-3 text-muted text-center border rounded">Mapbox Token not configured.</div>';
        return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const defaultCenter = (locations && locations.length > 0) 
        ? [locations[0].longitude, locations[0].latitude]
        : [-98.5795, 39.8283];

    if (!friendMap) {
        friendMap = new mapboxgl.Map({
            container: 'friend-map',
            style: getMapStyle(),
            center: defaultCenter,
            zoom: locations && locations.length > 0 ? 9 : 3
        });
        friendMap.addControl(new mapboxgl.NavigationControl(), 'top-right');
    } else {
        friendMarkers.forEach(m => m.remove());
        friendMarkers = [];

        if (locations && locations.length > 0) {
            friendMap.flyTo({
                center: [locations[0].longitude, locations[0].latitude],
                zoom: 9
            });
        }
    }

    if (locations) {
        locations.forEach(loc => {
            const popupHtml = `<strong>${loc.song_name || 'Entry'}</strong><br><small>${loc.date}</small>`;
            const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(popupHtml);

            const marker = new mapboxgl.Marker({ color: '#1db954' })
                .setLngLat([loc.longitude, loc.latitude])
                .setPopup(popup)
                .addTo(friendMap);

            friendMarkers.push(marker);
        });
    }
}