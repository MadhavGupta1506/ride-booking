var map = L.map('map').setView([23.2599, 77.4126], 13);

let markers = [];

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OpenStreetMap'
}).addTo(map);

function updateDriverLocations() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    $.ajax({
        url: 'http://localhost:8000/drivers',
        method: 'GET',
        dataType: 'json',
        success: function (data) {
            $.each(data, function (i, driver) {
                var marker = L.marker([driver.lat, driver.lng]).addTo(map);
                marker.bindPopup('<b>' + driver.name + '</b><br>Vehicle: ' + driver.vehicle);
                markers.push(marker);
            });
        },
        error: function (xhr, status, error) {
            console.error('Error fetching driver data:', error);
        }
    });
}

$(document).ready(function () {
    updateDriverLocations();

    $('#requestRide').on('click', function () {
        alert('Ride requested!');
    });
});

setInterval(updateDriverLocations, 8000);
$("#requestRide").on("click", function () {
    $.ajax({
        url: 'http://localhost:8000/request-ride',
        method: 'POST',
        dataType: 'json',
        data: JSON.stringify({
            pickup_lat: 23.2599,
            pickup_lng: 77.4126,
            dropoff_lat: 23.2500,
            dropoff_lng: 77.4200
        }),
        contentType: 'application/json',
        success: function (response) {
            alert('Ride requested successfully!');
        },
        error: function (xhr, status, error) {
            console.error('Error requesting ride:', error);
            alert('Failed to request ride. Please try again.');
        }
    });
});