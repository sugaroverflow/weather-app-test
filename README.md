# Weather App Dashboard

A monolithic weather app built with Flask that allows users to search for current weather conditions in cities around the world.

## Overview

This application consists of:
- A Flask backend that serves both the API and the frontend
- A HTML/CSS/JavaScript frontend
- Integration with the OpenWeatherMap API

## Project Structure

```
weather-app/
├── app.py                  # Main Flask application
├── templates/              # HTML templates
│   └── index.html          # Frontend interface
├── .env                    # Environment variables (not in repo)
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Setup Instructions

### Prerequisites
- Python 3.7+
- OpenWeatherMap API key

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your OpenWeatherMap API key:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   ```

### Running the Application

Run the Flask application:
```
python app.py
```

The application will be available at http://localhost:5000

## API Endpoints

### Get Current Weather
- **URL**: `/api/weather`
- **Method**: `GET`
- **Parameters**: `city` (required) - Name of the city
- **Response**: JSON object containing formatted weather data

### Health Check
- **URL**: `/api/health`
- **Method**: `GET`
- **Response**: `{"status": "ok"}`