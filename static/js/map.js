// ========== 1. GLOBAL VARIABLES AND CONSTANTS ==========

// Map instance and state
let map;
let activeLayer = 'precipitation'; // Default active layer

// API Keys
let defaultApiKey = 'c10bb3bd22f90d636baa008b1d375bd4'; // Default OpenWeatherMap key for testing
const mapboxToken = 'pk.eyJ1Ijoic3VnYXJvdmVyZmxvdyIsImEiOiJjbWFicmVmMWwwN2NmMnNvZ3Q3OXYyNmppIn0.SRF6ui8AZlt-edmUrKoNVQ';

// Markers and data tracking
let currentMarker;
let cityMarkers = []; // Store city markers for cleanup
let infoMarkers = []; // Store info markers for cleanup

// ========== 2. HELPER FUNCTIONS ==========

// Get AQI color based on value (1-5)
function getAqiColor(aqi) {
    const colors = [
        '#50F0E6', // 1: Good (Light blue)
        '#50CCAA', // 2: Fair (Teal)
        '#F0E641', // 3: Moderate (Yellow)
        '#FF5050', // 4: Poor (Red)
        '#960032'  // 5: Very Poor (Dark red)
    ];
    return colors[aqi - 1] || colors[0];
}

// Get AQI circle radius based on value (1-5)
function getAqiRadius(aqi) {
    // Radius increases with worse AQI
    return 24 + (aqi - 1) * 4;
}

// Get AQI description based on value (1-5)
function getAqiDescription(aqi) {
    const descriptions = [
        'Good: Air quality is satisfactory',
        'Fair: Air quality is acceptable',
        'Moderate: Health concerns for sensitive individuals',
        'Poor: Health effects for everyone',
        'Very Poor: Health alert, avoid outdoor activities'
    ];
    return descriptions[aqi - 1] || 'Unknown';
}

// Helper function to map OpenWeatherMap icon codes to Font Awesome icons
function getWeatherIconClass(iconCode) {
    const iconMap = {
        '01d': 'fas fa-sun',        // clear sky day
        '01n': 'fas fa-moon',       // clear sky night
        '02d': 'fas fa-cloud-sun',  // few clouds day
        '02n': 'fas fa-cloud-moon', // few clouds night
        '03d': 'fas fa-cloud',      // scattered clouds day
        '03n': 'fas fa-cloud',      // scattered clouds night
        '04d': 'fas fa-cloud-meatball', // broken clouds day
        '04n': 'fas fa-cloud-meatball', // broken clouds night
        '09d': 'fas fa-cloud-showers-heavy', // shower rain day
        '09n': 'fas fa-cloud-showers-heavy', // shower rain night
        '10d': 'fas fa-cloud-sun-rain', // rain day
        '10n': 'fas fa-cloud-moon-rain', // rain night
        '11d': 'fas fa-bolt',       // thunderstorm day
        '11n': 'fas fa-bolt',       // thunderstorm night
        '13d': 'fas fa-snowflake',  // snow day
        '13n': 'fas fa-snowflake',  // snow night
        '50d': 'fas fa-smog',       // mist day
        '50n': 'fas fa-smog'        // mist night
    };
    return iconMap[iconCode] || 'fas fa-question-circle'; // Default icon
}

// Calculate a bounding box around a point with a given radius in kilometers
function calculateBoundingBox(lat, lon, radiusKm) {
    // Earth's radius in kilometers
    const earthRadius = 6371;
    
    // Convert radius from kilometers to radians
    const radiusRad = radiusKm / earthRadius;
    
    // Convert latitude and longitude to radians
    const latRad = (lat * Math.PI) / 180;
    const lonRad = (lon * Math.PI) / 180;
    
    // Calculate min/max latitudes
    const minLat = latRad - radiusRad;
    const maxLat = latRad + radiusRad;
    
    // Calculate min/max longitudes
    const deltaLon = Math.asin(Math.sin(radiusRad) / Math.cos(latRad));
    const minLon = lonRad - deltaLon;
    const maxLon = lonRad + deltaLon;
    
    // Convert back to degrees
    return {
        minLat: (minLat * 180) / Math.PI,
        minLon: (minLon * 180) / Math.PI,
        maxLat: (maxLat * 180) / Math.PI,
        maxLon: (maxLon * 180) / Math.PI
    };
}

// ========== 3. MAP INITIALIZATION ==========

// Initialize the map when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Mapbox with token
    mapboxgl.accessToken = mapboxToken;
    
    // Create map instance
    map = new mapboxgl.Map({
        container: 'weather-map',
        style: 'mapbox://styles/mapbox/streets-v12', // More detailed style
        center: [-73.9857, 40.7484], // New York as default center
        zoom: 5, // Regional zoom level
        attributionControl: false
    });

    // Add navigation controls
    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    
    // Add Mapbox attribution in the bottom-right corner
    map.addControl(new mapboxgl.AttributionControl({
        compact: true
    }));
    
    // When the map is loaded, resize it and load the default layer
    map.on('load', function() {
        setTimeout(function() {
            map.resize();
            console.log('Map loaded and resized');
            
            // Load default layer (precipitation)
            loadWeatherLayers(-73.9857, 40.7484, defaultApiKey);
        }, 100);
    });
    
    // Add event listeners and set up UI controls
    setupResizeObservers();
    setupLayerControls();
});

// ========== 4. EVENT LISTENERS & UI SETUP ==========

// Set up resize observers for responsive map
function setupResizeObservers() {
    // Add a resize observer to handle container size changes
    const resizeObserver = new ResizeObserver(entries => {
        if (map) {
            map.resize();
        }
    });
    
    // Observe the map container and weather info section
    const mapContainer = document.getElementById('weather-map');
    const weatherInfo = document.getElementById('weather-info');
    
    if (mapContainer) {
        resizeObserver.observe(mapContainer);
    }
    
    if (weatherInfo) {
        resizeObserver.observe(weatherInfo);
    }
}

// Set up event listeners for layer control buttons
function setupLayerControls() {
    const layerButtons = document.querySelectorAll('.weather-layer-btn');
    
    // Set the initial active layer
    layerButtons.forEach(button => {
        if (button.getAttribute('data-layer') === 'precipitation') {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    layerButtons.forEach(button => {
        button.addEventListener('click', function() {
            const newLayer = this.getAttribute('data-layer');
            // Only proceed if the layer is actually changing
            if (newLayer === activeLayer && !map.getStyle().layers.some(l => l.id.startsWith('weather-') || l.id.startsWith('temperature-') || l.id.startsWith('aqi-'))) {
                 // If same layer clicked but no layers are visible (e.g., after an error), force reload
                 console.log('Forcing reload for the same layer as no relevant layers found.');
            } else if (newLayer === activeLayer) {
                console.log('Layer already active:', activeLayer);
                return; // Do nothing if the layer hasn't changed
            }

            // Remove active class from all buttons
            layerButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update active layer
            activeLayer = newLayer;
            console.log('Switching to layer:', activeLayer);
            
            // Reload layers if map is ready and coordinates exist
            if (map && map.isStyleLoaded() && window.lastSearchedCoords) {
                const { lat, lon } = window.lastSearchedCoords;
                const apiKey = window.currentApiKey || defaultApiKey;
                
                console.log('Reloading map with layer:', activeLayer);
                // Clear existing layers immediately before loading new ones
                clearMapLayers(); 
                // Use a minimal timeout to ensure UI update and prevent potential race conditions
                setTimeout(() => {
                    loadWeatherLayers(lat, lon, apiKey);
                }, 10); 
            } else {
                console.log('Map not ready or coordinates not available yet.');
                // Optionally queue the layer load if map isn't ready
                if (map && !map.isStyleLoaded()) {
                    map.once('load', () => {
                         if (window.lastSearchedCoords) {
                            const { lat, lon } = window.lastSearchedCoords;
                            const apiKey = window.currentApiKey || defaultApiKey;
                            loadWeatherLayers(lat, lon, apiKey);
                         }
                    });
                }
            }
        });
    });
}

// Function to center map on a specific location
function centerMapOnLocation(coordinates) {
    map.flyTo({
        center: [coordinates.lon, coordinates.lat],
        zoom: 5, // Regional zoom level
        duration: 2000, // Longer animation for smoother transition
        essential: true
    });
}

// Function to fetch and display weather data
async function showRegionalWeather(lat, lon, apiKey) {
    try {
        // Store the coordinates globally for layer switching
        window.lastSearchedCoords = { lat, lon };
        
        // Store the API key globally for layer switching
        window.currentApiKey = apiKey || defaultApiKey;
        
        // Load active layer
        await loadWeatherLayers(lat, lon, window.currentApiKey);
        
    } catch (error) {
        console.error('Error fetching weather data:', error);
    }
}

// ========== 5. LAYER MANAGEMENT FUNCTIONS ==========

// Helper function to clear all map layers and markers
function clearMapLayers() {
    console.log('Clearing existing map layers');
    
    // Remove existing marker if any
    if (currentMarker) {
        currentMarker.remove();
    }
    
    // Remove city markers
    cityMarkers.forEach(marker => marker.remove());
    cityMarkers = [];
    
    // Remove info markers
    infoMarkers.forEach(marker => marker.remove());
    infoMarkers = [];
    
    // Remove existing weather layers - be more thorough in cleanup
    try {
        // Check and remove all possible sources (needed to prevent duplicates)
        const possibleSources = [
            'weather-tiles', 'weather-tiles-cls', 'temperature-tiles', 
            'temperature-data', 'wind-data', 'air-quality-data'
        ];
        
        possibleSources.forEach(sourceId => {
            removeLayer(sourceId);
        });
    } catch (e) {
        console.error('Error during layer cleanup:', e);
    }
}

// Helper function to remove a specific layer and source
function removeLayer(sourceId) {
    try {
        if (map.getSource(sourceId)) {
            // Get all layers that use this source
            const style = map.getStyle();
            if (!style || !style.layers) return;
            
            const layersToRemove = style.layers
                .filter(layer => layer.source === sourceId)
                .map(layer => layer.id);
            
            // Remove each layer before removing the source
            layersToRemove.forEach(layerId => {
                if (map.getLayer(layerId)) {
                    map.removeLayer(layerId);
                }
            });
            
            // Remove the source
            map.removeSource(sourceId);
        }
    } catch (e) {
        console.warn(`Issue removing source ${sourceId}:`, e.message);
    }
}

// Load weather layers on the map
async function loadWeatherLayers(lat, lon, apiKey) {
    console.log('Loading weather layer:', activeLayer);
    
    // Wait for map to be fully loaded
    if (!map.loaded()) {
        console.log('Map not fully loaded, waiting...');
        map.once('load', function() {
            loadWeatherLayers(lat, lon, apiKey);
        });
        return;
    }
    
    // Clear all existing layers first
    clearMapLayers();
    
    try {
        // Load the active layer with error handling
        switch (activeLayer) {
            case 'precipitation':
                await loadPrecipitationLayer(lat, lon, apiKey);
                break;
            case 'temperature':
                await loadTemperatureLayer(lat, lon, apiKey);
                break;
            case 'air-quality':
                await loadAirQualityLayer(lat, lon, apiKey);
                break;
            default:
                await loadPrecipitationLayer(lat, lon, apiKey);
        }
        
        console.log('Layer loaded successfully:', activeLayer);
    } catch (error) {
        console.error('Error loading layer:', error);
    }
}

// ========== 6. WEATHER LAYER LOADING FUNCTIONS ==========

// Load precipitation layer
async function loadPrecipitationLayer(lat, lon, apiKey) {
    console.log('Adding precipitation layer');
    try {
        // Add precipitation layer - using both precipitation and precipitation_cls for better visualization
        if (!map.getSource('weather-tiles')) {
            map.addSource('weather-tiles', {
                'type': 'raster',
                'tiles': [
                    `https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${apiKey}`
                ],
                'tileSize': 256,
                'attribution': 'Weather data © OpenWeatherMap'
            });
        }
        
        if (!map.getLayer('weather-radar')) {
            map.addLayer({
                'id': 'weather-radar',
                'type': 'raster',
                'source': 'weather-tiles',
                'paint': {
                    'raster-opacity': 0.9 // Increased opacity
                }
            });
        }
        
        try {
            // Add precipitation_cls layer for better precipitation visualization
            if (!map.getSource('weather-tiles-cls')) {
                map.addSource('weather-tiles-cls', {
                    'type': 'raster',
                    'tiles': [
                        `https://tile.openweathermap.org/map/precipitation_cls/{z}/{x}/{y}.png?appid=${apiKey}`
                    ],
                    'tileSize': 256
                });
            }
            
            if (!map.getLayer('weather-radar-cls')) {
                map.addLayer({
                    'id': 'weather-radar-cls',
                    'type': 'raster',
                    'source': 'weather-tiles-cls',
                    'paint': {
                        'raster-opacity': 0.7
                    }
                });
            }
        } catch (clsError) {
            console.warn('Could not add cls layer:', clsError);
            // Continue if the second layer fails
        }
        
        // Add precipitation info markers
        await addPrecipitationInfoMarkers(lat, lon, apiKey);
        
        console.log('Precipitation layer added');
    } catch (error) {
        console.error('Error adding precipitation layer:', error);
    }
}

// Load temperature layer
async function loadTemperatureLayer(lat, lon, apiKey) {
    console.log('Adding temperature layer');
    try {
        // Add temperature raster layer for wider coverage
        if (!map.getSource('temperature-tiles')) {
            map.addSource('temperature-tiles', {
                'type': 'raster',
                'tiles': [
                    `https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${apiKey}`
                ],
                'tileSize': 256,
                'attribution': 'Weather data © OpenWeatherMap'
            });
        }
        
        if (!map.getLayer('temperature-raster')) {
            map.addLayer({
                'id': 'temperature-raster',
                'type': 'raster',
                'source': 'temperature-tiles',
                'paint': {
                    'raster-opacity': 0.8
                }
            });
        }
        
        // Add temperature info markers
        await addTemperatureInfoMarkers(lat, lon, apiKey);
        
        console.log('Temperature layer added');
    } catch (error) {
        console.error('Error creating temperature layer:', error);
    }
}

// Load air quality layer
async function loadAirQualityLayer(lat, lon, apiKey) {
    console.log('Adding air quality layer');
    try {
        // Create a grid of points for the air quality visualization
        const bbox = calculateBoundingBox(lat, lon, 300); // 300km radius
        
        // Generate a grid of points
        const gridSize = 12;
        const latStep = (bbox.maxLat - bbox.minLat) / gridSize;
        const lonStep = (bbox.maxLon - bbox.minLon) / gridSize;
        
        const gridPoints = [];
        for (let i = 0; i <= gridSize; i += 2) {
            for (let j = 0; j <= gridSize; j += 2) {
                gridPoints.push({
                    lat: bbox.minLat + i * latStep,
                    lon: bbox.minLon + j * lonStep
                });
            }
        }
        
        // Create AQI data from grid points
        const promises = gridPoints.map(async point => {
            try {
                const url = `https://api.openweathermap.org/data/2.5/air_pollution?lat=${point.lat}&lon=${point.lon}&appid=${apiKey}`;
                const response = await fetch(url);
                if (!response.ok) return null;
                
                const data = await response.json();
                // Basic validation of API response structure
                if (!data || !data.list || !data.list[0] || !data.list[0].main || typeof data.list[0].main.aqi === 'undefined') {
                    console.warn('Invalid AQI data structure received for', point);
                    return null;
                }
                return {
                    ...point,
                    aqi: data.list[0].main.aqi,
                    components: data.list[0].components
                };
            } catch (e) {
                console.error('Error fetching AQI for point:', point, e);
                return null;
            }
        });
        
        // Wait for all requests to complete
        const results = (await Promise.all(promises)).filter(point => point !== null);
        
        console.log(`Fetched ${results.length} valid AQI points out of ${gridPoints.length} attempts.`);

        // Add air quality visualization - using circle markers
        for (const point of results) {
            // Create a marker for this point
            const el = document.createElement('div');
            el.className = 'info-marker aqi-marker'; // Add base class
            
            // Get color and size based on AQI
            const color = getAqiColor(point.aqi);
            
            // Updated round marker structure
            el.innerHTML = `
                <div class="marker-content" style="background-color: ${color};">
                    <span class="marker-label">AQI</span>
                    <span class="marker-value">${point.aqi}</span>
                     <i class="fas fa-wind marker-icon"></i> 
                </div>
            `;
            
            // Create info content
            const content = document.createElement('div');
            content.className = 'info-popup';
            content.innerHTML = `
                <div class="info-content">
                    <h4>Air Quality Index: ${point.aqi}</h4>
                    <div class="aqi-description">${getAqiDescription(point.aqi)}</div>
                    <div class="aqi-components">
                        <div class="component-item">PM2.5: ${point.components.pm2_5.toFixed(1)} µg/m³</div>
                        <div class="component-item">PM10: ${point.components.pm10.toFixed(1)} µg/m³</div>
                        <div class="component-item">NO₂: ${point.components.no2.toFixed(1)} µg/m³</div>
                        <div class="component-item">O₃: ${point.components.o3.toFixed(1)} µg/m³</div>
                    </div>
                </div>
            `;
            
            // Create marker with popup
            const popup = new mapboxgl.Popup({ offset: 25 }).setDOMContent(content);
            const marker = new mapboxgl.Marker(el)
                .setLngLat([point.lon, point.lat])
                .setPopup(popup)
                .addTo(map);
                
            // Store marker for later cleanup
            infoMarkers.push(marker);
        }
        
        console.log('Air quality layer added');
    } catch (error) {
        console.error('Error creating air quality layer:', error);
    }
}

// Add precipitation info markers
async function addPrecipitationInfoMarkers(lat, lon, apiKey) {
    try {
        // Get a wider area bbox
        const bbox = calculateBoundingBox(lat, lon, 300); // 300km radius
        
        // Define strategic points within the bbox for markers
        const markerPoints = [
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.25, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.25 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.75, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.25 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.25, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.75 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.75, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.75 }
        ];
        
        // For each point, get precipitation data
        for (const point of markerPoints) {
            // Only add markers where there's precipitation
            const pointUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${point.lat}&lon=${point.lon}&units=metric&appid=${apiKey}`;
            const response = await fetch(pointUrl);
            if (response.ok) {
                const data = await response.json();
                
                // Only add markers where there's precipitation or clouds
                if (data.rain || data.snow || (data.clouds && data.clouds.all > 60)) {
                    // Create a precipitation info marker
                    const el = document.createElement('div');
                    el.className = 'precip-marker';
                    el.innerHTML = `
                        <div class="precip-icon">
                            <i class="fas fa-cloud-rain" style="color: #4287f5; font-size: 16px;"></i>
                        </div>
                    `;
                    
                    // Create info content
                    const content = document.createElement('div');
                    content.className = 'info-popup';
                    content.innerHTML = `
                        <div class="info-content">
                            <h4>${data.name || 'Area'}</h4>
                            <div class="info-item">
                                <img src="https://openweathermap.org/img/wn/${data.weather[0].icon}.png" alt="${data.weather[0].description}" style="width: 40px;">
                                <span>${data.weather[0].description}</span>
                            </div>
                            ${data.rain ? `<div class="info-value">Rain: ${data.rain['1h'] || data.rain['3h'] || 'Light'} mm</div>` : ''}
                            ${data.snow ? `<div class="info-value">Snow: ${data.snow['1h'] || data.snow['3h'] || 'Light'} mm</div>` : ''}
                            <div class="info-value">Clouds: ${data.clouds.all}%</div>
                            <div class="info-value">Humidity: ${data.main.humidity}%</div>
                        </div>
                    `;
                    
                    // Create marker with popup
                    const popup = new mapboxgl.Popup({ offset: 25 }).setDOMContent(content);
                    const marker = new mapboxgl.Marker(el)
                        .setLngLat([point.lon, point.lat])
                        .setPopup(popup)
                        .addTo(map);
                        
                    // Store marker for later cleanup
                    infoMarkers.push(marker);
                }
            }
        }
    } catch (error) {
        console.error('Error adding precipitation info markers:', error);
    }
}

// Add temperature info markers
async function addTemperatureInfoMarkers(lat, lon, apiKey) {
    try {
        // Get a wider area bbox
        const bbox = calculateBoundingBox(lat, lon, 300); // 300km radius
        
        // Define strategic points within the bbox for markers - Increased points
        const markerPoints = [
            // Center
            { lat: lat, lon: lon }, 
            // Inner Ring
            { lat: lat + 0.5, lon: lon + 0.5 },
            { lat: lat - 0.5, lon: lon - 0.5 },
            { lat: lat + 0.5, lon: lon - 0.5 },
            { lat: lat - 0.5, lon: lon + 0.5 },
            // Outer Ring (more spread out)
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.2, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.2 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.8, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.2 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.2, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.8 },
            { lat: bbox.minLat + (bbox.maxLat - bbox.minLat) * 0.8, lon: bbox.minLon + (bbox.maxLon - bbox.minLon) * 0.8 },
             // Additional points for better coverage
            { lat: lat + 1.0, lon: lon },
            { lat: lat - 1.0, lon: lon },
            { lat: lat, lon: lon + 1.0 },
            { lat: lat, lon: lon - 1.0 }
        ];
        
        // Limit markers to avoid clutter
        const maxMarkers = 8; 
        const pointsToFetch = markerPoints.slice(0, maxMarkers);

        // Fetch data concurrently
        const promises = pointsToFetch.map(async (point) => {
             const pointUrl = `https://api.openweathermap.org/data/2.5/weather?lat=${point.lat}&lon=${point.lon}&units=metric&appid=${apiKey}`;
            try {
                const response = await fetch(pointUrl);
                if (response.ok) {
                    return await response.json();
                }
            } catch (fetchError) {
                console.warn(`Failed to fetch temp data for ${point.lat}, ${point.lon}:`, fetchError);
            }
            return null; // Return null on failure
        });

        const results = (await Promise.all(promises)).filter(data => data !== null); // Filter out null results


        // Create markers from fetched data
        results.forEach(data => {
                // Create a temperature marker with the actual temperature
                const el = document.createElement('div');
                el.className = 'info-marker temp-marker'; // Add base class
                
                // Choose color based on temperature
                let color = '#3498db'; // Cold (blue)
                if (data.main.temp > 30) color = '#e74c3c'; // Hot (red)
                else if (data.main.temp > 20) color = '#f39c12'; // Warm (orange)
                else if (data.main.temp > 10) color = '#2ecc71'; // Mild (green)
                
                // Get appropriate weather icon
                const weatherIconClass = getWeatherIconClass(data.weather[0].icon);
                
                // Updated round marker structure
                el.innerHTML = `
                    <div class="marker-content" style="background-color: ${color};">
                        <span class="marker-label">${data.name || 'Area'}</span>
                        <span class="marker-value">${Math.round(data.main.temp)}°</span>
                        <i class="${weatherIconClass} marker-icon"></i>
                    </div>
                `;
                
                // Create info content
                const content = document.createElement('div');
                content.className = 'info-popup';
                content.innerHTML = `
                    <div class="info-content">
                        <h4>${data.name || 'Area'}</h4>
                        <div class="temp-details">
                            <div class="current-temp">${Math.round(data.main.temp)}°C</div>
                            <div class="feels-like">Feels like: ${Math.round(data.main.feels_like)}°C</div>
                        </div>
                        <div class="info-item">
                            <img src="https://openweathermap.org/img/wn/${data.weather[0].icon}.png" alt="${data.weather[0].description}" style="width: 40px;">
                            <span>${data.weather[0].description}</span>
                        </div>
                        <div class="minmax-temp">
                            <span>Min: ${Math.round(data.main.temp_min)}°C</span>
                            <span>Max: ${Math.round(data.main.temp_max)}°C</span>
                        </div>
                    </div>
                `;
                
                // Create marker with popup
                const popup = new mapboxgl.Popup({ offset: 25 }).setDOMContent(content);
                const marker = new mapboxgl.Marker(el)
                    .setLngLat([data.coord.lon, data.coord.lat])
                    .setPopup(popup)
                    .addTo(map);
                    
                // Store marker for later cleanup
                infoMarkers.push(marker);
            });
    } catch (error) {
        console.error('Error adding temperature info markers:', error);
    }
}

// Export functions for use in other files
window.centerMapOnLocation = centerMapOnLocation;
window.showRegionalWeather = showRegionalWeather;
window.map = map; // Make map accessible globally 