let moodMap;
let countryMarkers = {};
let selectedCountry = null;
let countryIndex = {};
let countriesList = [];
let geoLayer = null;

function initMap() {
    moodMap = L.map("map", {
        minZoom: 2,
        worldCopyJump: true,
    });

    moodMap.fitWorld();

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 6,
        attribution: "&copy; OpenStreetMap contributors",
    }).addTo(moodMap);

    fetch("/static/data/world.geojson")
        .then((response) => response.json())
        .then((geojson) => {
            geoLayer = L.geoJSON(geojson, {
                style: {
                    fillColor: "#7aa6ff",
                    fillOpacity: 0.3,
                    color: "#2f4f6f",
                    weight: 1,
                },
                onEachFeature: (feature, layer) => {
                    layer.on({
                        mouseover: () => layer.setStyle({ fillOpacity: 0.6 }),
                        mouseout: () => geoLayer && geoLayer.resetStyle(layer),
                        click: () => {
                            const code = feature.properties?.code || feature.id;
                            if (code) {
                                selectCountry(code);
                            }
                        },
                    });
                },
            }).addTo(moodMap);
            const bounds = geoLayer.getBounds();
            if (bounds.isValid()) {
                moodMap.fitBounds(bounds, { padding: [8, 8] });
            }
        });

    fetch("/api/countries/")
        .then((response) => response.json())
        .then((countries) => {
            countriesList = countries;
            countries.forEach((country) => {
                const emoji = country.latest_snapshot ? country.latest_snapshot.emoji : "😐";
                const marker = L.marker([country.centroid_lat, country.centroid_lng], {
                    icon: L.divIcon({
                        className: "emoji-marker",
                        html: emoji,
                    }),
                }).addTo(moodMap);
                marker.on("click", () => selectCountry(country.code));
                countryMarkers[country.code] = marker;
                const normalizedName = country.name.toLowerCase();
                countryIndex[normalizedName] = country.code;
                countryIndex[country.code.toLowerCase()] = country.code;
            });
            populateCountrySearch(countries);
        });

    connectMoodSocket();
}

function populateCountrySearch(countries) {
    const datalist = document.getElementById("country-options");
    if (!datalist) {
        return;
    }
    datalist.innerHTML = "";
    countries.forEach((country) => {
        const option = document.createElement("option");
        option.value = `${country.name} (${country.code})`;
        datalist.appendChild(option);
    });

    const input = document.getElementById("country-search");
    const button = document.getElementById("country-search-btn");
    if (button) {
        button.addEventListener("click", () => searchForCountry(input.value));
    }
    if (input) {
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                searchForCountry(input.value);
            }
        });
    }
}

function searchForCountry(value) {
    const query = value.trim();
    if (!query) {
        return;
    }
    const normalized = query.toLowerCase();
    const codeMatch = query.match(/\(([^)]+)\)\s*$/);
    const explicitCode = codeMatch ? codeMatch[1].trim().toLowerCase() : null;
    let code = explicitCode ? countryIndex[explicitCode] : countryIndex[normalized];
    if (!code) {
        const match = countriesList.find((country) =>
            country.name.toLowerCase().includes(normalized),
        );
        code = match ? match.code : null;
    }
    if (code) {
        selectCountry(code);
        const marker = countryMarkers[code];
        if (marker) {
            moodMap.setView(marker.getLatLng(), Math.max(moodMap.getZoom(), 4), { animate: true });
        }
    }
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
            marker.setIcon(
                L.divIcon({
                    className: "emoji-marker",
                    html: data.emoji || "😐",
                }),
            );
        }
        if (selectedCountry && data.country === selectedCountry) {
            selectCountry(selectedCountry);
        }
    };

    socket.onclose = () => {
        setTimeout(connectMoodSocket, 5000);
    };
}

document.addEventListener("DOMContentLoaded", initMap);
