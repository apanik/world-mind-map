let moodMap;
let countryMarkers = {};
let selectedCountry = null;

function initMap() {
    moodMap = new google.maps.Map(document.getElementById("map"), {
        center: { lat: 20, lng: 0 },
        zoom: 2,
        minZoom: 2,
        mapTypeControl: false,
        streetViewControl: false,
    });

    moodMap.data.loadGeoJson("/static/data/world.geojson");
    moodMap.data.setStyle({
        fillColor: "#7aa6ff",
        fillOpacity: 0.3,
        strokeColor: "#2f4f6f",
        strokeWeight: 1,
    });

    moodMap.data.addListener("mouseover", (event) => {
        moodMap.data.overrideStyle(event.feature, { fillOpacity: 0.6 });
    });
    moodMap.data.addListener("mouseout", (event) => {
        moodMap.data.revertStyle(event.feature);
    });

    moodMap.data.addListener("click", (event) => {
        const code = event.feature.getProperty("code") || event.feature.getProperty("id") || event.feature.getId();
        if (code) {
            selectCountry(code);
        }
    });

    fetch("/api/countries/")
        .then((response) => response.json())
        .then((countries) => {
            countries.forEach((country) => {
                const emoji = country.latest_snapshot ? country.latest_snapshot.emoji : "😐";
                const marker = new google.maps.Marker({
                    position: { lat: country.centroid_lat, lng: country.centroid_lng },
                    map: moodMap,
                    label: {
                        text: emoji,
                        fontSize: "18px",
                    },
                });
                marker.addListener("click", () => selectCountry(country.code));
                countryMarkers[country.code] = marker;
            });
        });

    connectMoodSocket();
}

function selectCountry(code) {
    selectedCountry = code;
    const url = `/country/${code}/panel/`;
    if (window.htmx) {
        htmx.ajax("GET", url, "#panel");
    } else {
        fetch(url)
            .then((response) => response.text())
            .then((html) => {
                document.getElementById("panel").innerHTML = html;
            });
    }
}

function connectMoodSocket() {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/moods/`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.country && countryMarkers[data.country]) {
            const marker = countryMarkers[data.country];
            marker.setLabel({ text: data.emoji || "😐", fontSize: "18px" });
        }
        if (selectedCountry && data.country === selectedCountry) {
            selectCountry(selectedCountry);
        }
    };

    socket.onclose = () => {
        setTimeout(connectMoodSocket, 5000);
    };
}

window.initMap = initMap;
