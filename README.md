# Weather Dashboard

A weather application built with Flask and Tailwind CSS that provides real-time weather conditions via the [Open Weather Map API](https://openweathermap.org/). 

## 📋 Table of Contents
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [API Endpoints](#-api-endpoints)
- [Features](#-features)
- [Local Map Implementation](#-local-map-implementation)
- [Testing](#-testing)
- [Demo Prompts](#-demo-prompts)

## 📂 Project Structure

```
weather-dashboard/
├── app.py                  # Main Flask application
├── static/                 # Static files directory
│   ├── js/                 # JavaScript files
│   │   ├── weather.js      # Weather data handling script
│   │   └── map.js          # Mapbox implementation script
│   └── vendor/             # Third-party libraries
│       └── mapbox-gl/      # Local Mapbox GL JS files
├── templates/              # HTML templates
│   └── index.html          # Frontend interface with Tailwind CSS
├── test_app.py             # Unit tests
├── .env                    # Environment variables (not in repo)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 🚀 Installation and Setup

**Prerequisites**
- Python 3.7+
- OpenWeatherMap API key (sign up at [openweathermap.org](https://openweathermap.org/api))

### Installation

1. Clone the repository:
   ```bash
   git clone https://gitlab.com/gitlab-da/sugaroverflow/weather-app.git
   cd weather-app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your OpenWeatherMap API key:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   ```

### Running the Application

```bash
# Development mode
python app.py

# Production mode (using gunicorn, install with pip first)
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

The application will be available at:
- Development: http://localhost:5000
- Production: http://localhost:8000

## 🔍 API Endpoints

### Get Current Weather
- **URL**: `/api/weather`
- **Method**: `GET`
- **Parameters**: `city` (required) - Name of the city
- **Response**: JSON object containing formatted weather data

### Get 5-Day Forecast
- **URL**: `/api/forecast`
- **Method**: `GET`
- **Parameters**: `city` (required) - Name of the city
- **Response**: JSON object containing daily forecasts for the next 5 days with weather descriptions and icons

### Get Air Quality
- **URL**: `/api/air-quality`
- **Method**: `GET`
- **Parameters**: `city` (required) - Name of the city
- **Response**: JSON object containing formatted air quality data

### Data Transformations
- **URL**: `/api/advanced-weather-processor`
- **Method**: `POST`
- **Body**: JSON object containing weather data and transformation operations
- **Response**: JSON object with original and transformed data

### Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Response**: `{"status": "ok", "version": "1.1.0"}`

## 🌟 Features

### Current Weather
Displays real-time weather information including temperature, humidity, pressure, and wind data.

### 5-Day Weather Forecast
Shows a 5-day forecast with daily weather conditions, complete with weather icons and temperature averages.

### Air Quality Information
Provides detailed air quality data with an easy-to-understand visual indicator and pollutant measurements.

## 🗺️ Local Map Implementation

For demo purposes and offline functionality, this project uses locally stored Mapbox GL JS files rather than loading them from CDN:

### Local Files Structure
- `static/vendor/mapbox-gl/mapbox-gl.js` - The Mapbox GL JavaScript library
- `static/vendor/mapbox-gl/mapbox-gl.css` - The Mapbox GL CSS styles

### Benefits of Local Implementation
- **Offline demos**: Present the application without requiring internet access
- **Performance**: Eliminates network dependency for loading map resources
- **Self-contained package**: All resources are included in the GitLab repository

### Mapbox Token
The application still requires a valid Mapbox access token for map tiles and services. This is configured in the map.js file:

```javascript
const mapboxToken = 'your_mapbox_token';
```

If you need to update this token, edit the `static/js/map.js` file.

## 🧪 Testing

Run the test suite with:
```bash
python -m unittest test_app.py
```

---
## 🚀 Demo prompts

Below are some ideas for how to extend this application using GitLab Duo. 
Note there is [a decoupled version of this application with a more complex architecture.](https://gitlab.com/gitlab-da/sugaroverflow/decoupled-weather-dashboard) This one is monolithic on purpose to reduce complexity.

### Adding features:
- Integrate with a mapping service to show geographic weather patterns
- Add a units toggle for metric and imperial
- Add a dark mode for theme switching

### Enhancements
- Add a caching startegy for API calls
- Deploy the site via CI/CD to AWS or GCP
- Add analytics to track performance.
- Add support for multiple languages