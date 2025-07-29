/**
 * Weather Dashboard JavaScript
 * Handles fetching and displaying weather data
 */

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const searchButton = document.getElementById('search-button');
    const cityInput = document.getElementById('city-input');
    const weatherInfo = document.getElementById('weather-info');
    const errorMessage = document.getElementById('error-message');

    // Theme toggle elements
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');

    // Elements for weather data
    const cityName = document.getElementById('city-name');
    const countryName = document.getElementById('country-name');
    const currentDate = document.getElementById('current-date');
    const currentTime = document.getElementById('current-time');
    const weatherDescription = document.getElementById('weather-description');
    const weatherIcon = document.getElementById('weather-icon');
    const temperature = document.getElementById('temperature');
    const feelsLike = document.getElementById('feels-like');
    const minMax = document.getElementById('min-max');
    const humidity = document.getElementById('humidity');
    const pressure = document.getElementById('pressure');
    const wind = document.getElementById('wind');
    const windDirection = document.getElementById('wind-direction');

    // Elements for air quality data
    const airQualityLevel = document.getElementById('air-quality-level');
    const airQualityDescription = document.getElementById('air-quality-description');
    const aqiIndicator = document.getElementById('aqi-indicator');
    const pm25 = document.getElementById('pm2_5');
    const pm10 = document.getElementById('pm10');
    const o3 = document.getElementById('o3');
    const no2 = document.getElementById('no2');

    // Element for forecast data
    const forecastContainer = document.getElementById('forecast-container');

    /**
     * Theme management functions
     */
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    }

    function setTheme(theme) {
        const html = document.documentElement;
        
        if (theme === 'dark') {
            html.classList.remove('light');
            html.classList.add('dark');
            themeIcon.className = 'fas fa-moon text-sm';
            themeText.textContent = 'Dark';
        } else {
            html.classList.remove('dark');
            html.classList.add('light');
            themeIcon.className = 'fas fa-sun text-sm';
            themeText.textContent = 'Light';
        }
        
        localStorage.setItem('theme', theme);
    }

    function toggleTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    }

    // Initialize theme
    initTheme();

    // Theme toggle event listener
    themeToggle.addEventListener('click', toggleTheme);

    /**
     * Format date from Unix timestamp
     * @param {number} timestamp - Unix timestamp
     * @returns {Object} - Formatted date and time
     */
    function formatDateTime(timestamp) {
        const date = new Date(timestamp * 1000);
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const timeOptions = {
            hour: '2-digit',
            minute: '2-digit'
        };

        return {
            date: date.toLocaleDateString('en-US', options),
            time: date.toLocaleTimeString('en-US', timeOptions)
        };
    }

    /**
     * Format date string to a more readable format
     * @param {string} dateStr - Date string in YYYY-MM-DD format
     * @returns {string} - Formatted date string
     */
    function formatDateString(dateStr) {
        const date = new Date(dateStr);
        const options = {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        };
        return date.toLocaleDateString('en-US', options);
    }

    /**
     * Convert wind degrees to direction
     * @param {number} degrees - Wind direction in degrees
     * @returns {string} - Wind direction as string (N, NE, E, etc.)
     */
    function getWindDirection(degrees) {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(degrees / 22.5) % 16;
        return directions[index];
    }

    /**
     * Set AQI indicator position based on AQI value
     * @param {number} aqi - Air Quality Index (1-5)
     */
    function setAqiIndicatorPosition(aqi) {
        // Values 1-5 correspond to positions 12.5%, 37.5%, 62.5%, 87.5%, 95%
        const positions = [null, 12.5, 37.5, 62.5, 87.5, 95];
        const position = positions[aqi] || 12.5; // Default to good if invalid
        aqiIndicator.style.left = `${position}%`;
    }

    /**
     * Show loading state
     */
    function showLoading() {
        cityInput.disabled = true;
        searchButton.disabled = true;
        searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        errorMessage.style.display = 'none';
    }

    /**
     * Reset loading state
     */
    function resetLoading() {
        cityInput.disabled = false;
        searchButton.disabled = false;
        searchButton.innerHTML = 'Search';
    }

    /**
     * Fetch weather data from API
     * @param {string} city - City name
     */
    async function getWeather(city) {
        try {
            showLoading();

            // Fetch weather data
            const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch weather data');
            }

            // Format date and time
            const dateTime = formatDateTime(data.timestamp);
            currentDate.textContent = dateTime.date;
            currentTime.textContent = dateTime.time;

            // Update weather information
            cityName.textContent = data.city;
            countryName.textContent = data.country;
            weatherDescription.textContent = data.weather.description;
            weatherIcon.src = `https://openweathermap.org/img/wn/${data.weather.icon}@2x.png`;
            weatherIcon.alt = data.weather.description;

            temperature.textContent = `${Math.round(data.temperature.current)}°C`;
            feelsLike.textContent = `${Math.round(data.temperature.feels_like)}°C`;
            minMax.textContent = `${Math.round(data.temperature.min)}°C / ${Math.round(data.temperature.max)}°C`;
            humidity.textContent = `${data.humidity}%`;
            pressure.textContent = `${data.pressure} hPa`;
            wind.textContent = `${data.wind.speed} m/s`;

            // Wind direction
            const direction = getWindDirection(data.wind.degrees);
            windDirection.textContent = direction;

            // Show weather info
            weatherInfo.style.display = 'block';

            // Get air quality and forecast data after weather data is loaded
            getAirQuality(city);
            getForecast(city);

        } catch (error) {
            // Show error message and hide weather info
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
            weatherInfo.style.display = 'none';
        } finally {
            resetLoading();
        }
    }

    /**
     * Fetch air quality data from API
     * @param {string} city - City name
     */
    async function getAirQuality(city) {
        try {
            const response = await fetch(`/api/air-quality?city=${encodeURIComponent(city)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch air quality data');
            }

            // Update air quality display
            airQualityLevel.textContent = data.air_quality_level;
            airQualityDescription.textContent = data.air_quality_description;

            // Set AQI indicator position
            setAqiIndicatorPosition(data.air_quality_index);

            // Update pollutant data
            if (data.components) {
                pm25.textContent = `${data.components.pm2_5.toFixed(1)} µg/m³`;
                pm10.textContent = `${data.components.pm10.toFixed(1)} µg/m³`;
                o3.textContent = `${data.components.o3.toFixed(1)} µg/m³`;
                no2.textContent = `${data.components.no2.toFixed(1)} µg/m³`;
            }

        } catch (error) {
            console.error('Error fetching air quality:', error);
            airQualityLevel.textContent = 'Unavailable';
            airQualityDescription.textContent = 'Air quality data could not be loaded.';

            // Reset pollutant values
            pm25.textContent = 'N/A';
            pm10.textContent = 'N/A';
            o3.textContent = 'N/A';
            no2.textContent = 'N/A';
        }
    }

    /**
     * Fetch 5-day forecast data from API
     * @param {string} city - City name
     */
    async function getForecast(city) {
        try {
            const response = await fetch(`/api/forecast?city=${encodeURIComponent(city)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch forecast data');
            }

            // Clear previous forecast data
            forecastContainer.innerHTML = '';

            // Create and append forecast cards
            data.forecasts.forEach(day => {
                const card = createForecastCard(day);
                forecastContainer.appendChild(card);
            });

        } catch (error) {
            console.error('Error fetching forecast:', error);
            forecastContainer.innerHTML = `
                <div class="col-span-5 text-center py-4">
                    <p class="text-gray-600 dark:text-gray-300">Forecast data could not be loaded.</p>
                </div>
            `;
        }
    }

    /**
     * Create a forecast card element
     * @param {Object} day - Daily forecast data
     * @returns {HTMLElement} - Forecast card element
     */
    function createForecastCard(day) {
        const card = document.createElement('div');
        card.className = 'bg-white dark:bg-gray-800 rounded-lg shadow-sm dark:shadow-card-dark border border-gray-100 dark:border-gray-600 p-4 text-center transition-all hover:shadow-card-hover dark:hover:shadow-card-hover-dark accent-line-top';

        const formattedDate = formatDateString(day.date);

        card.innerHTML = `
            <h4 class="font-medium text-primary-dark dark:text-white mb-2">${formattedDate}</h4>
            <div class="flex justify-center mb-1">
                <img src="https://openweathermap.org/img/wn/${day.weather.icon}@2x.png" 
                     alt="${day.weather.description}" 
                     class="w-16 h-16">
            </div>
            <p class="text-lg font-semibold text-primary-dark dark:text-white mb-1">${Math.round(day.temp)}°C</p>
            <p class="text-sm text-gray-600 dark:text-gray-300 capitalize mb-2">${day.weather.description}</p>
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
                <span><i class="fas fa-tint mr-1"></i> ${day.humidity}%</span>
                <span><i class="fas fa-wind mr-1"></i> ${day.wind_speed} m/s</span>
            </div>
        `;

        return card;
    }

    // Event listener for search button
    searchButton.addEventListener('click', function () {
        const city = cityInput.value.trim();
        if (city) {
            getWeather(city);
        } else {
            errorMessage.textContent = 'Please enter a city name';
            errorMessage.style.display = 'block';
        }
    });

    // Event listener for Enter key in input
    cityInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            const city = cityInput.value.trim();
            if (city) {
                getWeather(city);
            } else {
                errorMessage.textContent = 'Please enter a city name';
                errorMessage.style.display = 'block';
            }
        }
    });

    // Auto-focus on the input field when page loads
    cityInput.focus();
});