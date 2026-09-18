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
- [Testing](#-testing)
- [Demo Prompts](#-demo-prompts)

## 📂 Project Structure

```
weather-dashboard/
├── app.py                  # Main Flask application
├── static/                 # Static files directory
│   ├── js/                 # JavaScript files
│   │   └── weather.js      # Weather data handling script
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
- Add a caching strategy for API calls
- Deploy the site via CI/CD to AWS or GCP
- Add analytics to track performance.
- Add support for multiple languages